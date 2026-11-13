import io
import uuid
import pytest
from app.core.config import settings
from app.models.modification import ProposalItemStatus, ProposalBatchStatus


SAMPLE_CONTRACT_FOR_PROPOSALS = """
CONTRATO DE ARRENDAMIENTO MERCANTIL
Entre Arrendadora Central S.A. de C.V. y Servicios Rápidos S.A. de C.V.
PRIMERA. OBJETO: Arrendamiento de oficinas corporativas en Insurgentes Sur.
SEGUNDA. RENTA: Renta mensual de $60,000.00 M.N. pagadera los primeros cinco días.
TERCERA. JURISDICCIÓN: Para la interpretación se someten a los juzgados de la Ciudad de México.
CUARTA. PENA CONVENCIONAL: En caso de mora se aplicará una pena convencional equivalente al 150% del valor total.
QUINTA. RESCISIÓN UNILATERAL: El arrendador podrá rescindir a su entera discreción y sin necesidad de justificación.
SEXTA. FUERO ALTERNO: Las controversias se tramitarán ante los juzgados de Monterrey, Nuevo León.
"""


def test_generate_modification_proposals(client, lawyer_headers):
    """Prueba la generación de propuestas de redacción estructuradas sin invención de hechos."""
    # 1. Cargar contrato
    upload_res = client.post(
        f"{settings.API_V1_PREFIX}/documents/upload",
        files={"file": ("contrato_para_modificaciones.txt", io.BytesIO(SAMPLE_CONTRACT_FOR_PROPOSALS.encode("utf-8")), "text/plain")},
        data={"doc_type": "CONTRATO", "title": "Contrato para Generación de Modificaciones"},
        headers=lawyer_headers
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]

    # 2. Generar lote de propuestas
    gen_res = client.post(
        f"{settings.API_V1_PREFIX}/modifications/generate/{doc_id}",
        json={"title": "Lote de Revisión de Cláusulas 2026", "objective": "BALANCED"},
        headers=lawyer_headers
    )
    assert gen_res.status_code == 201
    batch_data = gen_res.json()

    assert batch_data["total_proposals"] >= 3
    assert batch_data["status"] == ProposalBatchStatus.PENDING_REVIEW
    items = batch_data["items"]

    # Verificar que las propuestas no inventan datos y usan placeholders [PENDIENTE: ...]
    has_placeholders = False
    for item in items:
        if item.get("missing_data_placeholders"):
            has_placeholders = True
            for ph in item["missing_data_placeholders"]:
                assert ph.startswith("[PENDIENTE:")

    assert has_placeholders is True

    # Verificar que existan opciones alternativas de redacción
    has_alternatives = any(len(it.get("alternative_options", [])) > 0 for it in items)
    assert has_alternatives is True

    # Verificar presencia de resumen de diffs
    has_diffs = any(it.get("diff_summary") is not None for it in items)
    assert has_diffs is True


def test_review_proposals_and_compile_new_version(client, lawyer_headers):
    """
    Prueba el flujo completo HITL:
    1. El abogado acepta y ajusta propuestas.
    2. El sistema compila la nueva versión (V2) sin tocar el original.
    3. Se emite aprobación con cédula profesional.
    """
    # 1. Cargar contrato y generar lote
    upload_res = client.post(
        f"{settings.API_V1_PREFIX}/documents/upload",
        files={"file": ("contrato_flujo_hitl.txt", io.BytesIO(SAMPLE_CONTRACT_FOR_PROPOSALS.encode("utf-8")), "text/plain")},
        data={"doc_type": "CONTRATO", "title": "Contrato para Flujo de Versión HITL"},
        headers=lawyer_headers
    )
    doc_id = upload_res.json()["id"]

    gen_res = client.post(
        f"{settings.API_V1_PREFIX}/modifications/generate/{doc_id}",
        json={"objective": "BALANCED"},
        headers=lawyer_headers
    )
    batch_id = gen_res.json()["id"]
    items = gen_res.json()["items"]
    assert len(items) >= 2

    # 2. El abogado acepta la primera propuesta
    prop_1_id = items[0]["id"]
    rev_1 = client.patch(
        f"{settings.API_V1_PREFIX}/modifications/proposals/{prop_1_id}/review",
        json={
            "status": "ACCEPTED",
            "reviewer_license": "98765432",
            "lawyer_notes": "Aprobada redacción equilibrada para unificar jurisdicción en CDMX."
        },
        headers=lawyer_headers
    )
    assert rev_1.status_code == 200
    assert rev_1.json()["status"] == ProposalItemStatus.ACCEPTED

    # 3. El abogado modifica y acepta la segunda propuesta con su propio texto
    prop_2_id = items[1]["id"]
    custom_lawyer_clause = "PENA CONVENCIONAL PACTADA: Se pacta una pena estricta del 10% sobre mensualidad insoluta."
    rev_2 = client.patch(
        f"{settings.API_V1_PREFIX}/modifications/proposals/{prop_2_id}/review",
        json={
            "status": "MODIFIED_BY_LAWYER",
            "lawyer_final_text": custom_lawyer_clause,
            "reviewer_license": "98765432",
            "lawyer_notes": "Ajustado el porcentaje al 10% por instrucción comercial del cliente."
        },
        headers=lawyer_headers
    )
    assert rev_2.status_code == 200
    assert rev_2.json()["status"] == ProposalItemStatus.MODIFIED_BY_LAWYER

    # 4. Compilar cambios aprobados en una Nueva Versión (V2)
    compile_res = client.post(
        f"{settings.API_V1_PREFIX}/modifications/batch/{batch_id}/apply-version",
        json={
            "version_notes": "Versión 2 revisada con jurisdicción CDMX y pena moderada al 10%.",
            "reviewer_license": "98765432"
        },
        headers=lawyer_headers
    )
    assert compile_res.status_code == 201
    version_data = compile_res.json()

    assert version_data["version_number"] == 2
    assert "Versión 2 revisada" in version_data["change_summary"]
    assert version_data["sha256_hash"] is not None

    # 5. Comprobar que el lote se marque como aplicado a versión 2
    batch_detail = client.get(f"{settings.API_V1_PREFIX}/modifications/batch/{batch_id}", headers=lawyer_headers).json()
    assert batch_detail["status"] == ProposalBatchStatus.APPLIED_TO_NEW_VERSION
    assert batch_detail["applied_version_number"] == 2


def test_export_document_docx_and_pdf(client, lawyer_headers):
    """Verifica la exportación nativa a DOCX (OpenXML) y PDF legal."""
    upload_res = client.post(
        f"{settings.API_V1_PREFIX}/documents/upload",
        files={"file": ("contrato_exportar.txt", io.BytesIO(SAMPLE_CONTRACT_FOR_PROPOSALS.encode("utf-8")), "text/plain")},
        data={"doc_type": "CONTRATO", "title": "Contrato para Pruebas de Exportación"},
        headers=lawyer_headers
    )
    doc_id = upload_res.json()["id"]

    # 1. Exportar a DOCX
    docx_res = client.get(f"{settings.API_V1_PREFIX}/modifications/export/docx/{doc_id}", headers=lawyer_headers)
    assert docx_res.status_code == 200
    assert docx_res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert "attachment; filename=" in docx_res.headers["content-disposition"]
    # Magic bytes de DOCX (Zip archive PK\x03\x04)
    assert docx_res.content.startswith(b"PK\x03\x04")
    assert len(docx_res.content) > 1000

    # 2. Exportar a PDF
    pdf_res = client.get(f"{settings.API_V1_PREFIX}/modifications/export/pdf/{doc_id}", headers=lawyer_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in pdf_res.headers["content-disposition"]
    # Magic bytes de PDF (%PDF-)
    assert pdf_res.content.startswith(b"%PDF-")
    assert len(pdf_res.content) > 1000


def test_superadmin_forbidden_from_proposals(client, auth_headers):
    """Verifica que el SUPER_ADMIN global tenga prohibido generar o consultar modificaciones privadas."""
    fake_id = str(uuid.uuid4())
    res = client.post(
        f"{settings.API_V1_PREFIX}/modifications/generate/{fake_id}",
        json={"objective": "BALANCED"},
        headers=auth_headers
    )
    assert res.status_code == 403
    assert "Acceso restringido por diseño" in res.json()["detail"]
