import io
import uuid
import pytest
from app.core.config import settings
from app.models.tenant import Tenant
from app.models.user import User
from app.models.document import Document
from app.models.rule import (
    LegalRule, RuleCategory, RuleSeverity, RuleOperator, RuleEvaluationStatus
)
from app.services.rules.rule_engine import DeterministicRuleEngine
from app.core.security import get_password_hash, LegalRoles, create_access_token


# =====================================================================
# 1. PRUEBAS UNITARIAS PURAS DEL MOTOR DETERMINISTA (SIN IA / SIN LLM)
# =====================================================================

def test_rule_engine_contains_all_keywords():
    engine = DeterministicRuleEngine()
    
    rule = LegalRule(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        rule_code="REG-JUR-001",
        name="Cláusula de Jurisdicción en CDMX",
        description="Obliga a someterse a los juzgados de la Ciudad de México",
        category=RuleCategory.JURISDICTION,
        severity=RuleSeverity.CRITICAL,
        is_active=True,
        scope={"doc_types": ["*"]},
        condition_definition={
            "operator": RuleOperator.CONTAINS_ALL_KEYWORDS,
            "parameters": {"keywords": ["tribunales", "ciudad de méxico"]}
        },
        expected_outcome="Sometimiento expreso a tribunales de CDMX."
    )

    doc = Document(id=uuid.uuid4(), doc_type="CONTRATO")

    # Caso A: Cumple (ambas frases presentes)
    text_ok = "Para cualquier controversia, las partes se someten expresamente a los tribunales competentes de la Ciudad de México."
    res_ok = engine.evaluate_rule(rule, text_ok, doc)
    assert res_ok["status"] == RuleEvaluationStatus.COMPLIANT
    assert "tribunales" in res_ok["matched_evidence"].lower()
    assert res_ok["failure_reason"] is None

    # Caso B: Incumple (falta una frase obligatoria)
    text_fail = "Las partes se someten a los tribunales de la Ciudad de Monterrey, Nuevo León."
    res_fail = engine.evaluate_rule(rule, text_fail, doc)
    assert res_fail["status"] == RuleEvaluationStatus.NON_COMPLIANT
    assert "ciudad de méxico" in res_fail["failure_reason"].lower()


def test_rule_engine_prohibits_keywords():
    engine = DeterministicRuleEngine()

    rule = LegalRule(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        rule_code="REG-PROH-001",
        name="Prohibición de Renuncia a Derechos Laborales",
        description="Prohíbe cláusulas que pretendan eximir al patrón de responsabilidades",
        category=RuleCategory.PROHIBITED_CLAUSE,
        severity=RuleSeverity.CRITICAL,
        is_active=True,
        scope={"doc_types": ["*"]},
        condition_definition={
            "operator": RuleOperator.PROHIBITS_KEYWORDS,
            "parameters": {"prohibited_keywords": ["renuncia irrevocable de prestaciones", "sin derecho a liquidación"]}
        },
        expected_outcome="No contener renuncia a prestaciones mínimas de ley."
    )

    doc = Document(id=uuid.uuid4(), doc_type="CONTRATO")

    # Caso A: Documento limpio -> Cumple
    clean_text = "El trabajador gozará de todas las prerrogativas contempladas en la Ley Federal del Trabajo."
    res_clean = engine.evaluate_rule(rule, clean_text, doc)
    assert res_clean["status"] == RuleEvaluationStatus.COMPLIANT
    assert res_clean["failure_reason"] is None

    # Caso B: Documento infractor -> Incumple determinista con evidencia exacta
    violating_text = "El prestador manifiesta su renuncia irrevocable de prestaciones laborales ordinarias y extraordinarias."
    res_viol = engine.evaluate_rule(rule, violating_text, doc)
    assert res_viol["status"] == RuleEvaluationStatus.NON_COMPLIANT
    assert "renuncia irrevocable de prestaciones" in res_viol["matched_evidence"].lower()
    assert "términos prohibidos" in res_viol["failure_reason"].lower()


def test_rule_engine_regex_match():
    engine = DeterministicRuleEngine()

    rule = LegalRule(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        rule_code="REG-PEN-001",
        name="Límite de Pena Convencional",
        description="Verifica formato de pena convencional con porcentaje explícito",
        category=RuleCategory.PENALTY,
        severity=RuleSeverity.HIGH,
        is_active=True,
        scope={"doc_types": ["*"]},
        condition_definition={
            "operator": RuleOperator.REGEX_MATCH,
            "parameters": {
                "regex_pattern": r"pena convencional(?: equivalente al)?\s*(\d+)\s*%",
                "expected_match": True
            }
        },
        expected_outcome="Expresar la pena convencional en porcentaje numérico."
    )

    doc = Document(id=uuid.uuid4(), doc_type="CONTRATO")

    # Con coincidencia
    text_with_penalty = "En caso de mora se aplicará una pena convencional equivalente al 15% del valor total."
    res = engine.evaluate_rule(rule, text_with_penalty, doc)
    assert res["status"] == RuleEvaluationStatus.COMPLIANT
    assert "15%" in res["matched_evidence"]

    # Sin coincidencia
    text_without = "En caso de mora se aplicarán las sanciones civiles pertinentes."
    res_no = engine.evaluate_rule(rule, text_without, doc)
    assert res_no["status"] == RuleEvaluationStatus.NON_COMPLIANT


def test_rule_engine_unverifiable_yields_pending_review():
    """
    REGLA CLAVE DEL SISTEMA:
    Cuando una regla no puede comprobarse automáticamente, DEBE registrar el resultado
    como PENDING_HUMAN_REVIEW y NUNCA como un falso incumplimiento confirmado.
    """
    engine = DeterministicRuleEngine()

    rule = LegalRule(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        rule_code="REG-NUM-002",
        name="Límite Máximo de Anticipo",
        description="El anticipo no debe rebasar $500,000 MXN",
        category=RuleCategory.AMOUNT_LIMIT,
        severity=RuleSeverity.HIGH,
        is_active=True,
        scope={"doc_types": ["*"]},
        condition_definition={
            "operator": RuleOperator.NUMERIC_RANGE,
            "parameters": {
                "regex_extractor": r"anticipo de \$([\d,]+(?:\.\d{2})?)",
                "max_value": 500000.0
            }
        },
        expected_outcome="Anticipo menor o igual a quinientos mil pesos."
    )

    doc = Document(id=uuid.uuid4(), doc_type="CONTRATO")

    # Documento ambiguo donde no se especifica el monto del anticipo con precisión determinista
    ambiguous_text = "Las partes convendrán el anticipo según el avance financiero del proyecto de obra."
    res = engine.evaluate_rule(rule, ambiguous_text, doc)

    # Debe ser PENDING_HUMAN_REVIEW y NO NON_COMPLIANT
    assert res["status"] == RuleEvaluationStatus.PENDING_HUMAN_REVIEW
    assert "revisión manual del abogado" in res["failure_reason"].lower()


def test_rule_engine_scope_filtering():
    engine = DeterministicRuleEngine()

    rule = LegalRule(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        rule_code="REG-DEM-001",
        name="Capítulo de Hechos en Demanda Mercantil",
        description="Aplica exclusivamente a Demandas",
        category=RuleCategory.MANDATORY_CLAUSE,
        severity=RuleSeverity.CRITICAL,
        is_active=True,
        scope={"doc_types": ["DEMANDA"]},
        condition_definition={
            "operator": RuleOperator.CONTAINS_ALL_KEYWORDS,
            "parameters": {"keywords": ["capítulo de hechos"]}
        },
        expected_outcome="Estructura formal de demanda mercantil."
    )

    # El documento es un CONTRATO, no una DEMANDA
    contract_doc = Document(id=uuid.uuid4(), doc_type="CONTRATO")
    res = engine.evaluate_rule(rule, "Contrato con capítulo de hechos", contract_doc)

    assert res["status"] == RuleEvaluationStatus.NOT_APPLICABLE
    assert "DEMANDA" in res["failure_reason"]


# =====================================================================
# 2. PRUEBAS DE INTEGRACIÓN API (ENDPOINT CRUD, VERSIONADO Y HITL)
# =====================================================================

def test_api_create_and_version_rule(client, lawyer_headers, db_session):
    """Crea una regla determinista y comprueba que se inicialice en versión 1."""
    rule_code = f"REG-TEST-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "rule_code": rule_code,
        "name": "Cláusula de Confidencialidad Rigurosa",
        "description": "Obligación de secreto industrial y profesional durante 5 años",
        "category": "CONFIDENTIALITY",
        "severity": "CRITICAL",
        "scope": {
            "doc_types": ["CONTRATO", "CONVENIO"]
        },
        "condition_definition": {
            "operator": "CONTAINS_ALL_KEYWORDS",
            "parameters": {"keywords": ["información confidencial", "secreto industrial"]}
        },
        "expected_outcome": "Pacto expreso de no divulgación por 5 años.",
        "legal_foundation": "Art. 82 de la Ley Federal de Protección a la Propiedad Industrial"
    }

    create_res = client.post(
        f"{settings.API_V1_PREFIX}/rules",
        json=payload,
        headers=lawyer_headers
    )
    assert create_res.status_code == 201
    rule_data = create_res.json()
    assert rule_data["rule_code"] == rule_code
    assert rule_data["version"] == 1
    assert rule_data["is_active"] is True
    rule_id = rule_data["id"]

    try:
        # Modificar regla -> Debe incrementar automáticamente a versión 2 y registrar motivo
        update_res = client.put(
            f"{settings.API_V1_PREFIX}/rules/{rule_id}",
            json={
                "name": "Cláusula de Confidencialidad y Secreto Industrial Reforzada",
                "change_reason": "Actualización por reforma legal a la LFPPI"
            },
            headers=lawyer_headers
        )
        assert update_res.status_code == 200
        updated_data = update_res.json()
        assert updated_data["version"] == 2
        assert "Reforzada" in updated_data["name"]

        # Consultar detalle y verificar versiones inmutables
        get_res = client.get(f"{settings.API_V1_PREFIX}/rules/{rule_id}", headers=lawyer_headers)
        assert get_res.status_code == 200
        detail = get_res.json()
        assert len(detail["versions"]) >= 2
        assert detail["versions"][0]["version_number"] == 2
        assert detail["versions"][1]["version_number"] == 1
    finally:
        from app.models.rule import LegalRule, RuleVersion
        db_session.query(RuleVersion).filter(RuleVersion.rule_id == rule_id).delete()
        db_session.query(LegalRule).filter(LegalRule.id == rule_id).delete()
        db_session.commit()


def test_api_evaluate_document_with_rules_and_hitl(client, lawyer_headers):
    """Sube un contrato de prueba, ejecuta la evaluación determinista y valida un hallazgo pendiente (HITL)."""
    # 1. Cargar documento de prueba
    sample_text = """
    CONTRATO DE PRESTACIÓN DE SERVICIOS PROFESIONALES
    En la Ciudad de México, celebran el presente contrato la empresa Alpha S.A. de C.V. y el consultor Lic. Juan Pérez.
    PRIMERA. OBJETO: Servicios de asesoría en ciberseguridad.
    SEGUNDA. HONORARIOS: Se pacta un pago único de $80,000.00 M.N.
    TERCERA. CONFIDENCIALIDAD: Toda la información confidencial compartida estará protegida bajo secreto industrial.
    CUARTA. JURISDICCIÓN: Para la interpretación y cumplimiento, se someten a la competencia de los tribunales de la Ciudad de México.
    """
    file_bytes = sample_text.strip().encode("utf-8")
    upload_res = client.post(
        f"{settings.API_V1_PREFIX}/documents/upload",
        files={"file": ("contrato_servicios_test.txt", io.BytesIO(file_bytes), "text/plain")},
        data={"doc_type": "CONTRATO", "title": "Contrato de Servicios para Auditoría Determinista"},
        headers=lawyer_headers
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["id"]

    # 2. Ejecutar evaluación determinista
    eval_res = client.post(
        f"{settings.API_V1_PREFIX}/rules/evaluate/{doc_id}",
        headers=lawyer_headers
    )
    assert eval_res.status_code == 201
    eval_data = eval_res.json()
    assert eval_data["total_rules_evaluated"] > 0
    assert "compliance_score" in eval_data
    assert len(eval_data["details"]) > 0

    # 3. Verificar que haya evidencias textuales capturadas
    details = eval_data["details"]
    compliant_items = [d for d in details if d["status"] == RuleEvaluationStatus.COMPLIANT]
    assert len(compliant_items) > 0
    assert compliant_items[0]["matched_evidence"] is not None

    # 4. Probar Human-in-the-Loop (HITL): Si hay un detalle pendiente o simular validación por abogado
    first_detail_id = details[0]["id"]
    verify_res = client.post(
        f"{settings.API_V1_PREFIX}/rules/evaluations/detail/{first_detail_id}/verify",
        json={
            "status": "COMPLIANT",
            "notes": "Validado y confirmado expresamente por el Abogado Titular conforme al Código de Comercio."
        },
        headers=lawyer_headers
    )
    assert verify_res.status_code == 200
    verified_data = verify_res.json()
    assert verified_data["status"] == "COMPLIANT"
    assert "Validado y confirmado" in verified_data["human_verification_notes"]
    assert verified_data["verified_at"] is not None


def test_api_multi_tenant_rule_isolation(client, lawyer_headers, setup_second_tenant, db_session):
    """Comprueba que el Despacho B no pueda ver ni acceder a las reglas del Despacho A."""
    # Despacho A crea una regla confidencial
    rule_code_a = f"REG-CONF-A-{uuid.uuid4().hex[:6].upper()}"
    res_a = client.post(
        f"{settings.API_V1_PREFIX}/rules",
        json={
            "rule_code": rule_code_a,
            "name": "Regla Estratégica Interna Despacho A",
            "description": "Criterio exclusivo de revisión para clientes corporativos del Despacho A",
            "category": "COMMERCIAL_REQUIREMENT",
            "severity": "HIGH",
            "scope": {"doc_types": ["*"]},
            "condition_definition": {
                "operator": "CONTAINS_ALL_KEYWORDS",
                "parameters": {"keywords": ["política corporativa interna"]}
            },
            "expected_outcome": "Cumplimiento de política interna."
        },
        headers=lawyer_headers
    )
    assert res_a.status_code == 201
    rule_id_a = res_a.json()["id"]

    try:
        # Despacho B intenta consultar la regla del Despacho A -> Debe ser 404 No Encontrada
        headers_b = setup_second_tenant["headers"]
        res_b = client.get(
            f"{settings.API_V1_PREFIX}/rules/{rule_id_a}",
            headers=headers_b
        )
        assert res_b.status_code == 404
    finally:
        from app.models.rule import LegalRule, RuleVersion
        db_session.query(RuleVersion).filter(RuleVersion.rule_id == rule_id_a).delete()
        db_session.query(LegalRule).filter(LegalRule.id == rule_id_a).delete()
        db_session.commit()


def test_api_superadmin_blocked_from_evaluating_private_doc(client, auth_headers):
    """
    Verifica que el SUPER_ADMIN global tenga prohibido evaluar documentos privados de clientes
    para proteger el secreto profesional y cumplir con el modelo de seguridad.
    """
    fake_doc_id = str(uuid.uuid4())
    res = client.post(
        f"{settings.API_V1_PREFIX}/rules/evaluate/{fake_doc_id}",
        headers=auth_headers  # auth_headers es SUPER_ADMIN
    )
    assert res.status_code == 403
    assert "Acceso restringido por diseño" in res.json()["detail"]
