import io
import uuid
import pytest
from app.core.config import settings
from app.models.advanced_analysis import FindingIssueType, FindingSeverity, FindingReviewStatus
from app.services.legal_sources.mexican_law_catalog import MexicanLawVerifier


# Texto contractual con 5 ERRORES JURÍDICOS CONOCIDOS
KNOWN_ERRORS_CONTRACT = """
CONTRATO DE ARRENDAMIENTO Y PRESTACIÓN DE SERVICIOS
Entre Arrendadora del Norte S.A. de C.V. y Servicios Rápidos S.A. de C.V.
PRIMERA. OBJETO: Arrendamiento de equipo tecnológico industrial.
SEGUNDA. PLAZO DE ENTREGA: El proveedor entregará el equipo dentro de los 30 días siguientes a la firma.
TERCERA. CONTRAPRESTACIÓN: Renta mensual de $50,000.00 M.N.
CUARTA. JURISDICCIÓN: Para la interpretación y cumplimiento, se someten expresamente a los tribunales de la Ciudad de México.
QUINTA. PENA CONVENCIONAL: En caso de mora, el arrendatario pagará una pena convencional equivalente al 150% del valor total del contrato.
SEXTA. FACULTAD DISCRECIONAL: El arrendador podrá rescindir el presente contrato a su entera discreción y sin necesidad de justificación alguna.
SÉPTIMA. TÉRMINO DE ATENCIÓN: El reporte de fallas deberá atenderse en un plazo de 15 días tras el aviso.
OCTAVA. FUERO ALTERNO: Cualquier controversia judicial se dirimirá ante los tribunales de Monterrey, Nuevo León.
NOVENA. FUNDAMENTO LEGAL: Este contrato se rige conforme al artículo 9999 de la ley mercantil inexistente y conforme al artículo 1093 del código de comercio.
"""

REMEDIATED_CONTRACT = """
CONTRATO DE ARRENDAMIENTO Y PRESTACIÓN DE SERVICIOS (VERSIÓN 2 REVISADA)
Entre Arrendadora del Norte S.A. de C.V. y Servicios Rápidos S.A. de C.V.
PRIMERA. OBJETO: Arrendamiento de equipo tecnológico industrial.
SEGUNDA. PLAZO DE ENTREGA: El proveedor entregará el equipo dentro de un plazo de 30 días siguientes a la firma.
TERCERA. CONTRAPRESTACIÓN: Renta mensual de $50,000.00 M.N.
CUARTA. JURISDICCIÓN: Para la interpretación y cumplimiento, las partes se someten a la competencia de los tribunales de la Ciudad de México, renunciando a cualquier otro fuero.
QUINTA. PENA CONVENCIONAL: En caso de mora culposa, se pacta una pena convencional equivalente al 15% de la mensualidad insoluta.
SEXTA. RESCISIÓN BILATERAL: Cualquiera de las partes podrá rescindir el contrato mediando notificación previa por escrito de 15 días ante incumplimiento grave.
SÉPTIMA. CONFIDENCIALIDAD: Toda la información técnica y comercial tendrá el carácter de secreto industrial protegido conforme a los artículos 82 y 85 de la Ley Federal de Protección a la Propiedad Industrial.
OCTAVA. DATOS PERSONALES: Las partes tratarán los datos personales conforme al aviso de privacidad y la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP).
"""


def test_mexican_law_verifier_catalog():
    """Verifica que el catálogo oficial identifique leyes vigentes y catalogue citas dudosas como por investigar."""
    # Caso A: Disposición vigente en catálogo oficial (Código de Comercio)
    ok_res = MexicanLawVerifier.verify_citation("artículo 1093 del código de comercio")
    assert ok_res["is_verified"] is True
    assert ok_res["validity_status"] == "VIGENTE_VERIFICADA"
    assert "Cámara de Diputados" in ok_res["official_source"] or "DOF" in ok_res["official_source"]
    assert ok_res["jurisdiction"] == "Federal"

    # Caso B: Artículo inexistente / fuera de rango
    out_of_range = MexicanLawVerifier.verify_citation("artículo 9999 del código de comercio")
    assert out_of_range["is_verified"] is False
    assert out_of_range["validity_status"] == "REQUIERE_INVESTIGACION_JURIDICA"

    # Caso C: Ley apócrifa o no catalogada
    fake_res = MexicanLawVerifier.verify_citation("artículo 5 de la ley de contratos ficticios")
    assert fake_res["is_verified"] is False
    assert fake_res["validity_status"] == "REQUIERE_INVESTIGACION_JURIDICA"


def test_analyze_document_with_known_errors(client, lawyer_headers):
    """
    Sube el documento con 5 errores jurídicos conocidos y valida que el motor
    los identifique con precisión, estructura y explicabilidad.
    """
    # 1. Cargar documento con errores conocidos
    file_bytes = KNOWN_ERRORS_CONTRACT.strip().encode("utf-8")
    upload_res = client.post(
        f"{settings.API_V1_PREFIX}/documents/upload",
        files={"file": ("contrato_con_errores_conocidos.txt", io.BytesIO(file_bytes), "text/plain")},
        data={"doc_type": "CONTRATO", "title": "Contrato de Prueba con Errores Críticos Conocidos"},
        headers=lawyer_headers
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]

    # 2. Ejecutar análisis jurídico avanzado
    analysis_res = client.post(
        f"{settings.API_V1_PREFIX}/advanced-analysis/analyze/{doc_id}",
        headers=lawyer_headers
    )
    assert analysis_res.status_code == 201
    analysis_data = analysis_res.json()

    assert analysis_data["findings_count"] >= 4
    assert analysis_data["critical_count"] >= 1
    assert analysis_data["overall_severity"] in ["CRITICAL", "HIGH"]
    assert analysis_data["overall_risk_score"] > 50.0  # Documento de alto riesgo

    findings = analysis_data["findings"]
    issue_types = [f["issue_type"] for f in findings]

    # Error 1: Contradicción de Jurisdicción detectada
    assert FindingIssueType.CONTRADICTION in issue_types
    contradiction_finding = next(f for f in findings if f["issue_type"] == FindingIssueType.CONTRADICTION)
    assert contradiction_finding["severity"] == FindingSeverity.CRITICAL
    assert "Ciudad de México" in contradiction_finding["description"]
    assert "Monterrey" in contradiction_finding["description"]
    assert contradiction_finding["legal_foundation"]["is_verified"] is True

    # Error 2: Pena Convencional Excesiva detectada (150%)
    assert FindingIssueType.EXCESSIVE_PENALTY in issue_types
    penalty_finding = next(f for f in findings if f["issue_type"] == FindingIssueType.EXCESSIVE_PENALTY)
    assert penalty_finding["severity"] in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]
    assert "150%" in penalty_finding["title"]
    assert "1843" in penalty_finding["legal_foundation"]["article"]

    # Error 3: Cláusula Potestativa / Unilateral detectada
    assert FindingIssueType.UNBALANCED_OBLIGATION in issue_types

    # Error 4: Cita Legal no Verificada / Incierta
    unverified_findings = [f for f in findings if f["issue_type"] == FindingIssueType.UNVERIFIED_CITATION]
    assert len(unverified_findings) > 0
    assert unverified_findings[0]["severity"] == FindingSeverity.REQUIRES_HUMAN_VALIDATION

    # 3. Comprobar descomposición de cláusulas
    clauses = analysis_data["clauses"]
    assert len(clauses) >= 7
    first_clause = clauses[0]
    assert "OBJETO" in first_clause["title"]
    assert len(first_clause["summary"]) > 5


def test_human_in_the_loop_finding_review(client, lawyer_headers):
    """Prueba que un abogado titular valide y dictamine una observación (HITL)."""
    # 1. Obtener última sesión de análisis
    # Primero cargamos un contrato simple
    simple_text = "CONTRATO MERCANTIL. PRIMERA. OBJETO: Venta de bienes. SEGUNDA. PAGO: $10,000 MXN."
    upload_res = client.post(
        f"{settings.API_V1_PREFIX}/documents/upload",
        files={"file": ("contrato_simple.txt", io.BytesIO(simple_text.encode("utf-8")), "text/plain")},
        data={"doc_type": "CONTRATO", "title": "Contrato Simple para Validación Humana"},
        headers=lawyer_headers
    )
    doc_id = upload_res.json()["id"]

    analysis_res = client.post(
        f"{settings.API_V1_PREFIX}/advanced-analysis/analyze/{doc_id}",
        headers=lawyer_headers
    )
    assert analysis_res.status_code == 201
    findings = analysis_res.json()["findings"]
    assert len(findings) > 0
    target_finding_id = findings[0]["id"]

    # 2. El abogado revisa la observación y confirma dictamen
    review_res = client.post(
        f"{settings.API_V1_PREFIX}/advanced-analysis/findings/{target_finding_id}/review",
        json={
            "review_status": "VALIDATED",
            "reviewer_license": "98765432",
            "reviewer_notes": "Observación validada formalmente por el Lic. Sofía Valenzuela. Procede sugerir addendum al cliente."
        },
        headers=lawyer_headers
    )
    assert review_res.status_code == 200
    reviewed_data = review_res.json()
    assert reviewed_data["review_status"] == "VALIDATED"
    assert reviewed_data["reviewer_license"] == "98765432"
    assert "Sofía Valenzuela" in reviewed_data["reviewer_notes"]
    assert reviewed_data["reviewed_at"] is not None


def test_version_comparison_and_risk_delta(client, lawyer_headers):
    """
    Compara la versión con errores (V1) contra la versión corregida (V2)
    y verifica que el delta de riesgos identifique riesgos mitigados y cláusulas añadidas.
    """
    # Creamos un documento base
    upload_res = client.post(
        f"{settings.API_V1_PREFIX}/documents/upload",
        files={"file": ("contrato_comparativa.txt", io.BytesIO(KNOWN_ERRORS_CONTRACT.encode("utf-8")), "text/plain")},
        data={"doc_type": "CONTRATO", "title": "Documento para Prueba de Comparativa"},
        headers=lawyer_headers
    )
    doc_id = upload_res.json()["id"]

    # Ejecutar comparativa entre V1 y V2
    comp_res = client.post(
        f"{settings.API_V1_PREFIX}/advanced-analysis/compare/{doc_id}",
        json={
            "base_text": KNOWN_ERRORS_CONTRACT,
            "compare_text": REMEDIATED_CONTRACT,
            "base_label": "Versión 1 (Borrador con Defectos)",
            "compare_label": "Versión 2 (Revisada y Remediada)"
        },
        headers=lawyer_headers
    )
    assert comp_res.status_code == 201
    comp_data = comp_res.json()

    # Comprobar que detecte cláusulas añadidas (Confidencialidad y Datos Personales)
    assert len(comp_data["added_clauses"]) > 0
    # Comprobar que detecte riesgos mitigados (la pena del 150% y la contradicción)
    risk_delta = comp_data["risk_delta"]
    assert "mitigated_risks" in risk_delta
    assert len(risk_delta["mitigated_risks"]) > 0

    assert "Comparativa entre" in comp_data["summary"]


def test_superadmin_blocked_from_advanced_analysis(client, auth_headers):
    """Verifica que el rol SUPER_ADMIN de la plataforma tenga prohibido por diseño acceder al análisis de clientes."""
    fake_id = str(uuid.uuid4())
    res = client.post(
        f"{settings.API_V1_PREFIX}/advanced-analysis/analyze/{fake_id}",
        headers=auth_headers
    )
    assert res.status_code == 403
    assert "Acceso restringido por diseño" in res.json()["detail"]
