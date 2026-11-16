import io
import pytest
from uuid import UUID
from datetime import datetime, timezone, timedelta
from app.models.workflow import WorkflowState, ApprovalScope, WorkflowApprovalRecord


@pytest.fixture(scope="module")
def workflow_doc_id(client, lawyer_headers, db_session):
    """Sube un documento de prueba y retorna su ID, limpiándolo al concluir el módulo."""
    from app.models.document import Document
    contract_text = (
        "CONTRATO DE PRESTACIÓN DE SERVICIOS JURÍDICOS Y CORPORATIVOS.\n"
        "PRIMERA.- OBJETO. El prestador brindará asesoría legal integral en la Ciudad de México.\n"
        "SEGUNDA.- HONORARIOS. El cliente cubrirá la cantidad pactada mensualmente.\n"
    )
    files = {"file": ("contrato_flujo.txt", io.BytesIO(contract_text.encode("utf-8")), "text/plain")}
    res = client.post(
        "/api/v1/documents/upload",
        files=files,
        data={"title": "Contrato para Flujo de Trabajo (Prueba)", "doc_type": "CONTRATO"},
        headers=lawyer_headers
    )
    assert res.status_code == 200
    doc_id = res.json()["id"]
    yield doc_id
    try:
        doc = db_session.query(Document).filter(Document.id == doc_id).first()
        if doc:
            db_session.delete(doc)
            db_session.commit()
    except Exception:
        db_session.rollback()


def test_get_or_create_workflow_lifecycle(client, lawyer_headers, workflow_doc_id):
    """Verifica la creación del workflow en estado RECIBIDO y transiciones sucesivas."""
    # 1. Obtener o crear workflow inicial
    res = client.get(f"/api/v1/workflow/document/{workflow_doc_id}", headers=lawyer_headers)
    assert res.status_code == 200
    data = res.json()
    workflow_id = data["id"]
    assert data["current_state"] == WorkflowState.RECEIVED
    assert len(data["transitions"]) >= 1
    assert data["transitions"][-1]["to_state"] == WorkflowState.RECEIVED

    # 2. Consultar transiciones permitidas desde RECEIVED
    trans_res = client.get(f"/api/v1/workflow/{workflow_id}/allowed-transitions", headers=lawyer_headers)
    assert trans_res.status_code == 200
    allowed = trans_res.json()
    target_states = [t["target_state"] for t in allowed]
    assert WorkflowState.PROCESSING in target_states or WorkflowState.PENDING_PROCESSING in target_states

    # 3. Transicionar a PROCESSING
    exec_res = client.post(
        f"/api/v1/workflow/{workflow_id}/transition",
        json={"target_state": WorkflowState.PROCESSING, "reason": "Iniciando extracción y OCR"},
        headers=lawyer_headers
    )
    assert exec_res.status_code == 200
    assert exec_res.json()["current_state"] == WorkflowState.PROCESSING

    # 4. Transicionar de PROCESSING a PENDING_REVIEW
    exec_res2 = client.post(
        f"/api/v1/workflow/{workflow_id}/transition",
        json={"target_state": WorkflowState.PENDING_REVIEW, "reason": "Análisis finalizado y listo para revisión"},
        headers=lawyer_headers
    )
    assert exec_res2.status_code == 200
    assert exec_res2.json()["current_state"] == WorkflowState.PENDING_REVIEW


def test_assign_team_and_deadline(client, lawyer_headers, workflow_doc_id):
    """Verifica asignación de abogado, revisor, asistente, prioridad y plazo fatal."""
    wf_res = client.get(f"/api/v1/workflow/document/{workflow_doc_id}", headers=lawyer_headers)
    workflow_id = wf_res.json()["id"]

    deadline = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    assign_res = client.post(
        f"/api/v1/workflow/{workflow_id}/assign",
        json={
            "priority": "HIGH",
            "deadline_at": deadline,
            "allow_assistant_approval": True
        },
        headers=lawyer_headers
    )
    assert assign_res.status_code == 200
    data = assign_res.json()
    assert data["priority"] == "HIGH"
    assert data["allow_assistant_approval"] is True
    assert data["is_overdue"] is False


def test_internal_comments_and_corrections(client, lawyer_headers, workflow_doc_id):
    """Verifica comentarios internos, solicitud de corrección y su resolución."""
    wf_res = client.get(f"/api/v1/workflow/document/{workflow_doc_id}", headers=lawyer_headers)
    workflow_id = wf_res.json()["id"]

    # 1. Agregar comentario interno
    comment_res = client.post(
        f"/api/v1/workflow/{workflow_id}/comments",
        json={
            "comment_text": "Revisar la cláusula de penalización moratoria antes de someter a firma.",
            "clause_reference": "Cláusula SEGUNDA",
            "is_internal_only": True
        },
        headers=lawyer_headers
    )
    assert comment_res.status_code == 201
    cdata = comment_res.json()
    assert "penalización" in cdata["comment_text"]
    assert cdata["clause_reference"] == "Cláusula SEGUNDA"

    # 2. Solicitar formalmente una corrección
    corr_res = client.post(
        f"/api/v1/workflow/{workflow_id}/corrections",
        json={
            "title": "Ajustar pena convencional al Código Civil",
            "description": "La pena estipulada supera el valor principal del contrato.",
            "target_clause": "Cláusula SEGUNDA"
        },
        headers=lawyer_headers
    )
    assert corr_res.status_code == 201
    corr_data = corr_res.json()
    corr_id = corr_data["id"]
    assert corr_data["status"] == "OPEN"

    # Verificar que el workflow se movió a IN_CORRECTION
    detail_res = client.get(f"/api/v1/workflow/{workflow_id}", headers=lawyer_headers)
    assert detail_res.json()["current_state"] == WorkflowState.IN_CORRECTION

    # 3. Resolver la corrección
    resolve_res = client.patch(
        f"/api/v1/workflow/corrections/{corr_id}/resolve",
        json={"resolution_notes": "Se limitó la pena convencional al monto legal máximo aplicable."},
        headers=lawyer_headers
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "RESOLVED"

    # Al resolverse todas las correcciones, regresa a PENDING_REVIEW
    detail_res2 = client.get(f"/api/v1/workflow/{workflow_id}", headers=lawyer_headers)
    assert detail_res2.json()["current_state"] == WorkflowState.PENDING_REVIEW


def test_definitive_approval_and_license_requirement(client, lawyer_headers, workflow_doc_id):
    """Verifica que la aprobación definitiva exija cédula profesional y mueva el estado a APROBADO."""
    wf_res = client.get(f"/api/v1/workflow/document/{workflow_doc_id}", headers=lawyer_headers)
    workflow_id = wf_res.json()["id"]

    # 1. Intentar aprobar definitivamente sin cédula profesional debe fallar si el usuario no tiene una registrada
    bad_approve = client.post(
        f"/api/v1/workflow/{workflow_id}/approve",
        json={"scope": ApprovalScope.DEFINITIVE_APPROVAL, "reviewer_license": "   "},
        headers=lawyer_headers
    )
    assert bad_approve.status_code in [400, 422]

    # 2. Aprobar con cédula profesional válida
    good_approve = client.post(
        f"/api/v1/workflow/{workflow_id}/approve",
        json={
            "scope": ApprovalScope.DEFINITIVE_APPROVAL,
            "reviewer_license": "CED-PROF-98765432",
            "notes": "Aprobado sin observaciones tras verificar subsanación de riesgos."
        },
        headers=lawyer_headers
    )
    assert good_approve.status_code == 201
    app_data = good_approve.json()
    assert app_data["status"] == "VALID"
    assert app_data["reviewer_license"] == "CED-PROF-98765432"
    assert app_data["scope"] == ApprovalScope.DEFINITIVE_APPROVAL

    # El workflow pasa a APPROVED
    detail = client.get(f"/api/v1/workflow/{workflow_id}", headers=lawyer_headers).json()
    assert detail["current_state"] == WorkflowState.APPROVED
    assert len(detail["approvals"]) >= 1


def test_invalidation_of_approvals_on_content_change(client, lawyer_headers, workflow_doc_id):
    """
    Regla crítica: Los cambios posteriores a una aprobación deben invalidar esa aprobación
    cuando afecten el contenido aprobado.
    """
    # 1. Obtener y aprobar el documento en v1
    wf_res = client.get(f"/api/v1/workflow/document/{workflow_doc_id}", headers=lawyer_headers)
    workflow_id = wf_res.json()["id"]

    approve_res = client.post(
        f"/api/v1/workflow/{workflow_id}/approve",
        json={
            "scope": ApprovalScope.DEFINITIVE_APPROVAL,
            "reviewer_license": "CED-PROF-11223344",
            "notes": "Aprobación de la versión 1"
        },
        headers=lawyer_headers
    )
    assert approve_res.status_code == 201
    app_id = approve_res.json()["id"]

    # 2. Generar y compilar una nueva versión (v2) que modifica el contenido
    # Generar lote de propuestas
    batch_res = client.post(
        f"/api/v1/modifications/generate/{workflow_doc_id}",
        json={"title": "Modificación posterior a la aprobación", "objective": "BALANCED"},
        headers=lawyer_headers
    )
    assert batch_res.status_code == 201
    batch_id = batch_res.json()["id"]

    # Aceptar la primera propuesta
    prop_id = batch_res.json()["items"][0]["id"]
    client.patch(
        f"/api/v1/modifications/proposals/{prop_id}/review",
        json={"status": "ACCEPTED", "reviewer_license": "CED-PROF-11223344"},
        headers=lawyer_headers
    )

    # Compilar nueva versión oficial (V2)
    compile_res = client.post(
        f"/api/v1/modifications/batch/{batch_id}/apply-version",
        json={"version_notes": "Modificación de cláusulas posterior a la aprobación previa", "reviewer_license": "CED-PROF-11223344"},
        headers=lawyer_headers
    )
    assert compile_res.status_code == 201
    new_version_num = compile_res.json()["version_number"]
    assert new_version_num >= 2

    # 3. Comprobar que la aprobación previa fue invalidada automáticamente
    detail_res = client.get(f"/api/v1/workflow/{workflow_id}", headers=lawyer_headers)
    assert detail_res.status_code == 200
    wf_data = detail_res.json()

    # El estado del workflow ya NO es APPROVED (regresa a IN_CORRECTION)
    assert wf_data["current_state"] == WorkflowState.IN_CORRECTION

    # La aprobación previa tiene status INVALIDATED_BY_CONTENT_CHANGE
    invalidated_apps = [
        a for a in wf_data["approvals"]
        if a["id"] == app_id and a["status"] == "INVALIDATED_BY_CONTENT_CHANGE"
    ]
    assert len(invalidated_apps) == 1
    assert invalidated_apps[0]["invalidated_by_version"] == new_version_num


def test_superadmin_blocked_from_workflow(client, auth_headers):
    """Verifica que SUPER_ADMIN tenga prohibido el acceso a expedientes de flujo de trabajo privados."""
    fake_doc_id = "00000000-0000-0000-0000-000000000001"
    res = client.get(f"/api/v1/workflow/document/{fake_doc_id}", headers=auth_headers)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


def test_ai_cannot_approve_documents_rejection(db_session, workflow_doc_id):
    """Verifica la regla estricta: La IA no puede aprobar documentos."""
    from app.services.workflow.approval_service import ApprovalService
    from app.services.workflow.workflow_service import WorkflowService
    from app.models.user import User
    from app.core.errors import ValidationException

    # Mock user con rol AI
    ai_user = User(
        id=None,
        email="ai_agent@system.local",
        full_name="Agente IA Drafter",
        role="AI",
        tenant_id=UUID("938678d9-ba23-4927-8a32-0ba461db4493")
    )
    service = WorkflowService(db_session)
    wf = service.get_or_create_workflow(
        tenant_id=UUID("938678d9-ba23-4927-8a32-0ba461db4493"),
        user=User(role="ASSOCIATE_LAWYER", tenant_id=UUID("938678d9-ba23-4927-8a32-0ba461db4493")),
        document_id=UUID(workflow_doc_id)
    )

    approval_srv = ApprovalService(db_session)
    with pytest.raises(ValidationException) as exc_info:
        approval_srv.submit_approval(
            workflow=wf,
            user=ai_user,
            scope=ApprovalScope.DEFINITIVE_APPROVAL,
            reviewer_license="CED-PROF-1111"
        )
    assert "La IA no tiene personalidad jurídica" in str(exc_info.value)


def test_assistant_approval_restrictions(db_session, workflow_doc_id):
    """
    Verifica que los asistentes no puedan aprobar documentos definitivos
    salvo que la política allow_assistant_approval esté explícitamente activa.
    """
    from app.services.workflow.approval_service import ApprovalService
    from app.services.workflow.workflow_service import WorkflowService
    from app.models.user import User
    from app.core.errors import ForbiddenException
    import uuid

    assistant_user = User(
        id=uuid.uuid4(),
        email=f"asistente_{uuid.uuid4().hex[:6]}@despacho.mx",
        hashed_password="hashed_pw_test",
        full_name="Pasante Jurídico Juan",
        role="LEGAL_ASSISTANT",
        tenant_id=UUID("938678d9-ba23-4927-8a32-0ba461db4493")
    )
    db_session.add(assistant_user)
    db_session.commit()

    try:
        service = WorkflowService(db_session)
        wf = service.get_or_create_workflow(
            tenant_id=UUID("938678d9-ba23-4927-8a32-0ba461db4493"),
            user=User(role="ASSOCIATE_LAWYER", tenant_id=UUID("938678d9-ba23-4927-8a32-0ba461db4493")),
            document_id=UUID(workflow_doc_id)
        )

        # 1. Con allow_assistant_approval=False, debe fallar con ForbiddenException
        wf.allow_assistant_approval = False
        approval_srv = ApprovalService(db_session)
        with pytest.raises(ForbiddenException) as exc_info:
            approval_srv.submit_approval(
                workflow=wf,
                user=assistant_user,
                scope=ApprovalScope.DEFINITIVE_APPROVAL,
                reviewer_license="CED-PASANTE-123"
            )
        assert "asistentes jurídicos no están facultados" in str(exc_info.value)

        # 2. Con política allow_assistant_approval=True, se permite
        wf.allow_assistant_approval = True
        app_record = approval_srv.submit_approval(
            workflow=wf,
            user=assistant_user,
            scope=ApprovalScope.DEFINITIVE_APPROVAL,
            reviewer_license="CED-PASANTE-123",
            notes="Aprobado por asistente bajo delegación expresa"
        )
        assert app_record.status == "VALID"
        assert app_record.reviewer_license == "CED-PASANTE-123"
    finally:
        db_session.delete(assistant_user)
        db_session.commit()


def test_notifications_system(client, lawyer_headers):
    """Verifica la consulta de notificaciones, contador y marcado como leída."""
    # 1. Consultar lista de notificaciones
    res = client.get("/api/v1/workflow/notifications/list", headers=lawyer_headers)
    assert res.status_code == 200
    notifs = res.json()
    assert isinstance(notifs, list)

    # 2. Consultar contador no leído
    count_res = client.get("/api/v1/workflow/notifications/unread-count", headers=lawyer_headers)
    assert count_res.status_code == 200
    assert "unread_count" in count_res.json()

    # 3. Marcar todas como leídas
    read_all = client.post("/api/v1/workflow/notifications/read-all", headers=lawyer_headers)
    assert read_all.status_code == 200
    assert "marked_read_count" in read_all.json()
