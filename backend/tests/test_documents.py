import io
import uuid
import pytest
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash, LegalRoles, create_access_token


def test_upload_and_extract_document(client, lawyer_headers):
    """Prueba la carga, extracción de texto y metadatos de un contrato mexicano."""
    contract_text = """
    CONTRATO DE ARRENDAMIENTO MERCANTIL
    En la Ciudad de México, a los 15 de enero de 2026, celebran el presente contrato:
    Por una parte, como ARRENDADOR: Inmobiliaria Reforma S.A. de C.V.
    Por la otra parte, como ARRENDATARIO: Servicios Legales del Centro S.C.
    PRIMERA. OBJETO: El ARRENDADOR otorga en arrendamiento el inmueble ubicado en Av. Insurgentes Sur 1602.
    SEGUNDA. RENTA: El ARRENDATARIO pagará la cantidad de $45,000.00 M.N. mensuales.
    TERCERA. VIGENCIA: El plazo de vigencia forzosa de doce meses para ambas partes.
    CUARTA. JURISDICCIÓN: Para la interpretación y cumplimiento, se someten a la competencia de los tribunales de la Ciudad de México.
    Firmado por el apoderado legal con cédula profesional número 55443322.
    """
    file_bytes = contract_text.encode("utf-8")
    files = {"file": ("contrato_arrendamiento.txt", io.BytesIO(file_bytes), "text/plain")}
    data = {
        "title": "Contrato de Arrendamiento Insurgentes 2026",
        "doc_type": "CONTRATO"
    }

    response = client.post("/api/v1/documents/upload", files=files, data=data, headers=lawyer_headers)
    assert response.status_code == 200
    doc_data = response.json()
    assert doc_data["title"] == "Contrato de Arrendamiento Insurgentes 2026"
    assert doc_data["doc_type"] == "CONTRATO"
    assert doc_data["is_original"] is True
    assert len(doc_data["sha256_hash"]) == 64
    
    # Verificar metadatos extraídos
    meta = doc_data["metadata_record"]
    assert meta is not None
    assert "$45,000.00 M.N." in meta["amounts"] or "$45,000.00" in str(meta["amounts"])
    assert "15 de enero de 2026" in meta["doc_date"]

    doc_id = doc_data["id"]

    # Vista previa
    preview_res = client.get(f"/api/v1/documents/{doc_id}/preview", headers=lawyer_headers)
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert "CONTRATO DE ARRENDAMIENTO" in preview_data["raw_text"]

    # Búsqueda por contenido de texto
    search_res = client.get("/api/v1/documents?query=Insurgentes", headers=lawyer_headers)
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert search_data["total"] >= 1
    assert any(d["id"] == doc_id for d in search_data["items"])


def test_superadmin_blocked_from_document_vault(client, auth_headers):
    """
    Verifica que el SUPER_ADMIN maestro tenga prohibido el acceso a
    documentos confidenciales de los despachos (Gobernanza y Privacidad).
    """
    content = b"DOCUMENTO DE CLIENTE PRIVADO"
    files = {"file": ("privado.txt", io.BytesIO(content), "text/plain")}
    response = client.post(
        "/api/v1/documents/upload",
        files=files,
        data={"title": "Documento Privado", "doc_type": "CONTRATO"},
        headers=auth_headers
    )
    assert response.status_code == 403
    error_data = response.json()
    assert error_data["error"]["code"] == "FORBIDDEN"


def test_horizontal_isolation_tenant_b_blocked(client, lawyer_headers, setup_second_tenant):
    """
    Verifica que un usuario del Despacho B no pueda acceder ni consultar
    un documento perteneciente al Despacho A (Protección contra IDOR).
    """
    # 1. Cargar documento en Despacho A
    content = b"DOCUMENTO CONFIDENCIAL DESPACHO A - CASO ULTRA SECRETO"
    files = {"file": ("secreto_a.txt", io.BytesIO(content), "text/plain")}
    res_a = client.post(
        "/api/v1/documents/upload",
        files=files,
        data={"title": "Documento Confidencial A", "doc_type": "DEMANDA"},
        headers=lawyer_headers
    )
    assert res_a.status_code == 200
    doc_a_id = res_a.json()["id"]

    # 2. Intentar leer documento de Despacho A usando credenciales de Despacho B
    headers_b = setup_second_tenant["headers"]
    res_b = client.get(f"/api/v1/documents/{doc_a_id}", headers=headers_b)
    
    # Debe ser denegado con 404 (para no revelar existencia) o 403
    assert res_b.status_code in [403, 404]

    # 3. Intentar descargar documento de Despacho A desde Despacho B
    download_res_b = client.get(f"/api/v1/documents/{doc_a_id}/download", headers=headers_b)
    assert download_res_b.status_code in [403, 404]


def test_create_document_version(client, lawyer_headers):
    """Verifica que crear una nueva versión no sobreescriba el original."""
    # Documento v1
    v1_content = b"VERSION 1 ORIGINAL DEL CONVENIO MODIFICATORIO"
    files_v1 = {"file": ("convenio.txt", io.BytesIO(v1_content), "text/plain")}
    res_v1 = client.post(
        "/api/v1/documents/upload",
        files=files_v1,
        data={"title": "Convenio Modificatorio", "doc_type": "CONVENIO"},
        headers=lawyer_headers
    )
    assert res_v1.status_code == 200
    doc_id = res_v1.json()["id"]
    original_hash = res_v1.json()["sha256_hash"]

    # Crear v2
    v2_content = b"VERSION 2 CON CORRECCIONES DEL ABOGADO REVISOR"
    files_v2 = {"file": ("convenio_v2.txt", io.BytesIO(v2_content), "text/plain")}
    res_v2 = client.post(
        f"/api/v1/documents/{doc_id}/versions",
        files=files_v2,
        data={"change_summary": "Ajuste de cláusula de penalidad convencional"},
        headers=lawyer_headers
    )
    assert res_v2.status_code == 200
    v2_data = res_v2.json()
    assert v2_data["version_number"] == 2
    assert v2_data["sha256_hash"] != original_hash

    # Verificar que el documento principal sigue conservando su hash original inmutable
    doc_detail = client.get(f"/api/v1/documents/{doc_id}", headers=lawyer_headers).json()
    assert doc_detail["sha256_hash"] == original_hash
    assert len(doc_detail["versions"]) == 1


def test_version_creation_invalidates_prior_approvals(client, lawyer_headers):
    """Verifica que la creación de una nueva versión invalide automáticamente aprobaciones previas."""
    # 1. Cargar documento original
    v1_content = b"DOCUMENTO DE PRUEBA DE INVALIDACION DE APROBACION"
    files_v1 = {"file": ("contrato_aprobacion.txt", io.BytesIO(v1_content), "text/plain")}
    res_v1 = client.post(
        "/api/v1/documents/upload",
        files=files_v1,
        data={"title": "Contrato Sujeto a Aprobacion", "doc_type": "CONTRATO"},
        headers=lawyer_headers
    )
    assert res_v1.status_code == 200
    doc_id = res_v1.json()["id"]

    # 2. Inicializar workflow
    wf_res = client.get(f"/api/v1/workflow/document/{doc_id}", headers=lawyer_headers)
    assert wf_res.status_code == 200
    wf_id = wf_res.json()["id"]

    # 3. Emitir aprobación definitiva con Cédula
    app_res = client.post(
        f"/api/v1/workflow/{wf_id}/approve",
        json={"reviewer_license": "12345678", "notes": "Aprobación inicial válida", "scope": "DEFINITIVE_APPROVAL"},
        headers=lawyer_headers
    )
    assert app_res.status_code == 201
    assert app_res.json()["status"] == "VALID"

    # Verificar que el workflow está en estado APPROVED
    wf_detail = client.get(f"/api/v1/workflow/{wf_id}", headers=lawyer_headers).json()
    assert wf_detail["current_state"] == "APPROVED"

    # 4. Crear versión 2 del documento
    v2_content = b"DOCUMENTO MODIFICADO VERSION 2 QUE DEBE INVALIDAR"
    files_v2 = {"file": ("contrato_v2.txt", io.BytesIO(v2_content), "text/plain")}
    res_v2 = client.post(
        f"/api/v1/documents/{doc_id}/versions",
        files=files_v2,
        data={"change_summary": "Modificación sustancial posterior a visto bueno"},
        headers=lawyer_headers
    )
    assert res_v2.status_code == 200

    # 5. Comprobar que la aprobación previa fue invalidada y el workflow regresó a IN_CORRECTION
    wf_after = client.get(f"/api/v1/workflow/{wf_id}", headers=lawyer_headers).json()
    assert wf_after["current_state"] == "IN_CORRECTION"
    approvals = wf_after["approvals"]
    assert len(approvals) >= 1
    prior_app = approvals[0]
    assert prior_app["status"] == "INVALIDATED_BY_CONTENT_CHANGE"
    assert "Modificación sustancial" in str(prior_app["invalidation_reason"])
