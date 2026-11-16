import io
import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.security import create_access_token, LegalRoles, get_password_hash
from app.models.tenant import Tenant
from app.models.user import User
from app.models.case import Case
from app.models.document import Document

client = TestClient(app)


@pytest.fixture
def seeded_despacho(db_session):
    return db_session.query(Tenant).filter(Tenant.slug == "despacho-demo").first()


def test_1_unauthenticated_request_fails(seeded_despacho):
    """1. Usuario no autenticado: debe retornar 401 Unauthorized."""
    res = client.get("/api/v1/documents")
    assert res.status_code == 401
    assert "detail" in res.json() or "error" in res.json()


def test_2_valid_token_authorized_user(seeded_despacho, db_session):
    """2. Usuario con token válido: debe retornar 200 OK con la lista de documentos."""
    user = db_session.query(User).filter(User.email == "abogado@bufetemexico.demo").first()
    token = create_access_token({"sub": str(user.id), "tenant_id": str(seeded_despacho.id), "role": user.role})
    
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data


def test_3_expired_token_fails(seeded_despacho, db_session):
    """3. Usuario con token expirado: debe retornar 401 Unauthorized."""
    user = db_session.query(User).filter(User.email == "abogado@bufetemexico.demo").first()
    expired_token = create_access_token(
        {"sub": str(user.id), "tenant_id": str(seeded_despacho.id), "role": user.role},
        expires_delta=timedelta(minutes=-10)  # Expirado en el pasado
    )
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401


def test_4_admin_despacho_access(seeded_despacho, db_session):
    """4. Admin del despacho: puede consultar todos los documentos del tenant (200 OK)."""
    admin_user = db_session.query(User).filter(User.email == "admin@bufetemexico.demo").first()
    assert admin_user is not None
    token = create_access_token({"sub": str(admin_user.id), "tenant_id": str(seeded_despacho.id), "role": admin_user.role})
    
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "items" in res.json()


def test_5_lawyer_access(seeded_despacho, db_session):
    """5. Lawyer: puede consultar documentos del despacho (200 OK)."""
    lawyer_user = db_session.query(User).filter(User.email == "abogado@bufetemexico.demo").first()
    assert lawyer_user is not None
    token = create_access_token({"sub": str(lawyer_user.id), "tenant_id": str(seeded_despacho.id), "role": lawyer_user.role})
    
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_6_reviewer_access(seeded_despacho, db_session):
    """6. Reviewer: puede consultar documentos para auditoría y revisión (200 OK)."""
    reviewer_user = db_session.query(User).filter(User.email == "revisor@bufetemexico.demo").first()
    assert reviewer_user is not None
    token = create_access_token({"sub": str(reviewer_user.id), "tenant_id": str(seeded_despacho.id), "role": reviewer_user.role})
    
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_7_assistant_access(seeded_despacho, db_session):
    """7. Assistant: puede consultar documentos del despacho (200 OK)."""
    assistant_user = db_session.query(User).filter(User.email == "asistente@bufetemexico.demo").first()
    assert assistant_user is not None
    token = create_access_token({"sub": str(assistant_user.id), "tenant_id": str(seeded_despacho.id), "role": assistant_user.role})
    
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200


def test_8_user_without_tenant_forbidden(seeded_despacho, db_session):
    """8. Usuario sin despacho asignado: debe retornar 403 Forbidden."""
    # Creamos un usuario de prueba y simulamos token sin tenant_id
    orphan_user = db_session.query(User).filter(User.email == "asistente@bufetemexico.demo").first()
    token_no_tenant = create_access_token({
        "sub": str(orphan_user.id),
        "email": orphan_user.email,
        "tenant_id": "",
        "role": orphan_user.role
    })
    
    # Mocking get_current_user o usando servicio directamente con tenant_id=None
    from app.services.document_service import DocumentService
    from app.core.errors import ForbiddenException
    
    with pytest.raises(ForbiddenException) as excinfo:
        DocumentService.search_documents(
            db=db_session,
            tenant_id=None,
            user_role="LAWYER"
        )
    assert "despacho asignado" in str(excinfo.value)


def test_9_user_of_another_tenant_cannot_see_tenant_a_docs(seeded_despacho, setup_second_tenant, db_session):
    """9. Usuario de otro despacho: aislamiento horizontal estricto (404 al intentar IDOR directo)."""
    # 1. Obtener documento de Despacho A
    doc_a = db_session.query(Document).filter(Document.tenant_id == seeded_despacho.id).first()
    assert doc_a is not None
    
    # 2. Token de Abogado en Despacho B
    user_b = setup_second_tenant["user"]
    token_b = create_access_token({
        "sub": str(user_b.id),
        "email": user_b.email,
        "tenant_id": str(user_b.tenant_id),
        "role": user_b.role
    })
    
    # 3. Intentar consultar documento del Despacho A desde Despacho B
    res = client.get(f"/api/v1/documents/{doc_a.id}", headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 404
    assert "no pertenece a este despacho" in res.json()["error"]["message"]
    
    # 4. Listado desde Despacho B no debe incluir documentos de Despacho A
    res_list = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {token_b}"})
    assert res_list.status_code == 200
    doc_ids_returned = [d["id"] for d in res_list.json()["items"]]
    assert str(doc_a.id) not in doc_ids_returned


def test_10_user_without_permission_on_case_forbidden(seeded_despacho, db_session):
    """10. Usuario sin permiso sobre un expediente específico: debe retornar 403 Forbidden."""
    # Crear un expediente asignado exclusivamente al Abogado Titular A
    lead_lawyer = db_session.query(User).filter(User.email == "abogado@bufetemexico.demo").first()
    restricted_case = Case(
        tenant_id=seeded_despacho.id,
        client_id=None,
        lead_lawyer_id=lead_lawyer.id,
        case_number=f"EXP-CONFIDENTIAL-{uuid.uuid4().hex[:6]}",
        title="Expediente Confidencial de Acceso Restringido",
        matter="PENAL",
        state="CDMX",
        status="ACTIVO"
    )
    # Asociar a cliente demo
    from app.models.client import Client
    demo_client = db_session.query(Client).filter(Client.tenant_id == seeded_despacho.id).first()
    if not demo_client:
        demo_client = Client(tenant_id=seeded_despacho.id, name="Cliente Confidencial", rfc="XAXX010101000")
        db_session.add(demo_client)
        db_session.commit()
    restricted_case.client_id = demo_client.id
    
    db_session.add(restricted_case)
    db_session.commit()
    db_session.refresh(restricted_case)

    try:
        # El asistente intenta consultar los documentos de este expediente restringido
        assistant_user = db_session.query(User).filter(User.email == "asistente@bufetemexico.demo").first()
        token_assistant = create_access_token({
            "sub": str(assistant_user.id),
            "tenant_id": str(seeded_despacho.id),
            "role": assistant_user.role
        })

        res = client.get(
            f"/api/v1/documents?case_id={restricted_case.id}",
            headers={"Authorization": f"Bearer {token_assistant}"}
        )
        assert res.status_code == 403
        assert "No cuenta con permisos asignados para consultar documentos de este expediente" in res.json()["error"]["message"]
    finally:
        db_session.delete(restricted_case)
        db_session.commit()
