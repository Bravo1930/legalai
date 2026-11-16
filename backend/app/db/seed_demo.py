import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.core.security import LegalRoles
from app.db.base import (
    Tenant, User, Client, Case, LegalMatter, CaseStatus,
    Document, DocumentMetadata, DocumentClassification,
    DocumentWorkflow, WorkflowState, WorkflowTransition,
    WorkflowApprovalRecord, ApprovalScope,
    AdvancedAnalysisSession, LegalFinding, FindingSeverity, FindingReviewStatus, FindingIssueType,
    AuditLog
)


def seed_demo_legal_data(db: Session, tenant_id: uuid.UUID):
    """
    Siembra datos de demostración ricos y verosímiles de la práctica jurídica en México:
    - 4 Clientes (Personas Morales y Físicas).
    - 4 Expedientes Judiciales (Civil, Familiar, Penal, Mercantil).
    - 6 Documentos indexados en bóveda inmutable con metadatos WORM.
    - Flujos de trabajo con asignación de abogados, transiciones y aprobaciones formales.
    - Hallazgos jurídicos y riesgos contractuales conforme al marco normativo mexicano.
    - Bitácora forense y actividad reciente.
    
    Controlado por settings.SEED_DEMO (SEED_DEMO=true en .env).
    Idempotente: si los datos de demo ya existen para este tenant, no se duplican.
    """
    if not settings.SEED_DEMO:
        logger.info("SEED_DEMO está desactivado en la configuración. Omitiendo datos de demostración.")
        return

    # Verificar si ya existen expedientes de demostración para este despacho
    existing_case = db.query(Case).filter(
        Case.tenant_id == tenant_id,
        Case.case_number == "DEMO-EXP-CIV-2026/104"
    ).first()
    if existing_case:
        logger.info("Los datos de demostración ya existen para este despacho. Omitiendo siembra.")
        return

    logger.info("Sembrando datos de demostración jurídica para el despacho...")

    # 1. Recuperar los abogados del despacho demo
    admin_lawyer = db.query(User).filter(User.tenant_id == tenant_id, User.email == "admin@bufetemexico.demo").first()
    senior_lawyer = db.query(User).filter(User.tenant_id == tenant_id, User.email == "abogado@bufetemexico.demo").first()
    reviewer_lawyer = db.query(User).filter(User.tenant_id == tenant_id, User.email == "revisor@bufetemexico.demo").first()
    assistant_user = db.query(User).filter(User.tenant_id == tenant_id, User.email == "asistente@bufetemexico.demo").first()

    default_actor_id = senior_lawyer.id if senior_lawyer else (admin_lawyer.id if admin_lawyer else None)

    # 2. Clientes (Empresas y Personas Físicas)
    client_inmobiliaria = Client(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Inmobiliaria Reforma Capital S.A. de C.V.",
        rfc="IRC180320AB3",
        client_type="PERSONA_MORAL",
        contact_email="apoderado@reformacapital.mx",
        contact_phone="+52 55 5280 1200",
        address="Paseo de la Reforma 222, Piso 18, Cuauhtémoc, CDMX"
    )
    client_logistica = Client(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Operadora Logística del Norte S.A.P.I. de C.V.",
        rfc="OLN150711XZ9",
        client_type="PERSONA_MORAL",
        contact_email="direccion.juridica@logisticanorte.com.mx",
        contact_phone="+52 81 8345 9000",
        address="Av. Fundidora 501, Obrera, Monterrey, N.L."
    )
    client_dra_elena = Client(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Dra. Elena Ramos Carvajal",
        rfc="RACE820415KT2",
        curp="RACE820415MMDFRN01",
        client_type="PERSONA_FISICA",
        contact_email="elena.ramos@medicosmexico.org",
        contact_phone="+52 55 5658 1122",
        address="Insurgentes Sur 1450, Crédito Constructor, Benito Juárez, CDMX"
    )
    client_ing_garza = Client(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        name="Ing. Fernando Garza Benítez",
        rfc="GABF751103M42",
        client_type="PERSONA_FISICA",
        contact_email="fgarza@tecnologiasgarza.mx",
        contact_phone="+52 55 5100 4433",
        address="Campos Elíseos 400, Polanco, Miguel Hidalgo, CDMX"
    )

    db.add_all([client_inmobiliaria, client_logistica, client_dra_elena, client_ing_garza])
    db.flush()

    # 3. Expedientes Jurídicos (Civil, Familiar, Penal, Mercantil)
    now = datetime.now(timezone.utc)
    
    case_civil = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        client_id=client_inmobiliaria.id,
        lead_lawyer_id=senior_lawyer.id if senior_lawyer else None,
        case_number="DEMO-EXP-CIV-2026/104",
        title="Juicio Ordinario Civil de Cumplimiento de Contrato de Arrendamiento Inmobiliario",
        description="Controversia sobre rescisión forzosa, cobro de rentas vencidas y entrega material del inmueble comercial en Reforma 222.",
        matter=LegalMatter.CIVIL,
        jurisdiction="CDMX",
        state="Ciudad de México",
        court_authority="Juzgado 14o de lo Civil del Poder Judicial de la CDMX",
        status=CaseStatus.ACTIVO,
        created_at=now - timedelta(days=25)
    )

    case_familiar = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        client_id=client_dra_elena.id,
        lead_lawyer_id=admin_lawyer.id if admin_lawyer else None,
        case_number="DEMO-EXP-FAM-2026/089",
        title="Controversia Familiar sobre Guarda, Custodia y Liquidación de Sociedad Conyugal",
        description="Procedimiento de convenio regulador transaccional con partición equitativa de masa hereditaria y bienes conyugales.",
        matter=LegalMatter.FAMILIAR,
        jurisdiction="CDMX",
        state="Ciudad de México",
        court_authority="Juzgado 8o Familiar de Proceso Oral de la CDMX",
        status=CaseStatus.ACTIVO,
        created_at=now - timedelta(days=18)
    )

    case_penal = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        client_id=client_ing_garza.id,
        lead_lawyer_id=reviewer_lawyer.id if reviewer_lawyer else None,
        case_number="DEMO-EXP-PEN-2026/042",
        title="Carpeta Judicial por Administración Fraudulenta y Fraude Mercantil Específico",
        description="Denuncia penal y querella procesal en defensa patrimonial por disposición no autorizada de activos corporativos.",
        matter=LegalMatter.PENAL,
        jurisdiction="FEDERAL",
        state="Ciudad de México",
        court_authority="Sala de Control Penal del Reclusorio Norte CDMX",
        status=CaseStatus.EN_TRAMITE,
        created_at=now - timedelta(days=35)
    )

    case_mercantil = Case(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        client_id=client_logistica.id,
        lead_lawyer_id=senior_lawyer.id if senior_lawyer else None,
        case_number="DEMO-EXP-MER-2026/215",
        title="Juicio Ejecutivo Mercantil Oral por Cobro de Pagaré Corporativo",
        description="Juicio oral mercantil para ejecución judicial de pagaré mercantil por $4,850,000 MXN derivado de fletes y logística.",
        matter=LegalMatter.MERCANTIL,
        jurisdiction="FEDERAL",
        state="Nuevo León",
        court_authority="Juzgado 2o de Distrito en Materia de Juicios Orales Mercantiles",
        status=CaseStatus.ACTIVO,
        created_at=now - timedelta(days=12)
    )

    db.add_all([case_civil, case_familiar, case_penal, case_mercantil])
    db.flush()

    # 4. Documentos en Bóveda WORM con Hashes SHA-256
    def make_hash(seed_text: str) -> str:
        return hashlib.sha256(seed_text.encode("utf-8")).hexdigest()

    doc1_content = (
        "CONTRATO DE ARRENDAMIENTO INMOBILIARIO COMERCIAL que celebran Inmobiliaria Reforma Capital S.A. de C.V. "
        "en calidad de Arrendador, y Corporativo Gastronómico S.A. de C.V. como Arrendatario. "
        "CLÁUSULA DÉCIMA CUARTA. PENA CONVENCIONAL. En caso de incumplimiento, el arrendatario pagará una pena de 100% "
        "del valor total del contrato sin perjuicio de daños y perjuicios. "
        "CLÁUSULA VIGÉSIMA. JURISDICCIÓN. Las partes se someten a la jurisdicción de los Tribunales de la Ciudad de México."
    )
    doc1 = Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case_civil.id,
        client_id=client_inmobiliaria.id,
        uploaded_by_id=senior_lawyer.id if senior_lawyer else default_actor_id,
        title="Contrato de Arrendamiento Inmobiliario Comercial Reforma 222",
        filename="Contrato_Arrendamiento_Reforma_2026.pdf",
        file_size_bytes=1048576,
        mime_type="application/pdf",
        sha256_hash=make_hash(doc1_content),
        storage_path=f"storage/tenants/{tenant_id}/docs/Contrato_Arrendamiento_Reforma_2026.pdf",
        doc_type=DocumentClassification.CONTRATO,
        is_original=True,
        is_confidential=False,
        page_count=12,
        created_at=now - timedelta(days=20)
    )

    doc2_content = (
        "CONVENIO TRANSACCIONAL DE DIVORCIO VOLUNTARIO Y DISOLUCIÓN DE SOCIEDAD CONYUGAL. "
        "Celebran la Dra. Elena Ramos Carvajal y el Sr. Mauricio Peña Garza ante el Juzgado Octavo de lo Familiar. "
        "CLÁUSULA TERCERA. PENSIÓN Y ALIMENTOS. Se conviene una pensión compensatoria definitiva y liquidación de inmueble conyugal."
    )
    doc2 = Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case_familiar.id,
        client_id=client_dra_elena.id,
        uploaded_by_id=admin_lawyer.id if admin_lawyer else default_actor_id,
        title="Convenio Transaccional y Partición de Masa Conyugal",
        filename="Convenio_Familiar_Ramos_2026.pdf",
        file_size_bytes=524288,
        mime_type="application/pdf",
        sha256_hash=make_hash(doc2_content),
        storage_path=f"storage/tenants/{tenant_id}/docs/Convenio_Familiar_Ramos_2026.pdf",
        doc_type=DocumentClassification.CONVENIO,
        is_original=True,
        is_confidential=True,
        page_count=8,
        created_at=now - timedelta(days=14)
    )

    doc3_content = (
        "ESCRITO DE QUERELLA Y DENUNCIA PENAL POR FRAUDE MERCANTIL Y ADMINISTRACIÓN FRAUDULENTA. "
        "Comparece el Ing. Fernando Garza Benítez denunciando la distracción de $12,500,000 pesos de la tesorería de la persona moral."
    )
    doc3 = Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case_penal.id,
        client_id=client_ing_garza.id,
        uploaded_by_id=reviewer_lawyer.id if reviewer_lawyer else default_actor_id,
        title="Escrito Inicial de Querella Penal por Fraude Patrimonial",
        filename="Querella_Penal_Fraude_Garza.pdf",
        file_size_bytes=2097152,
        mime_type="application/pdf",
        sha256_hash=make_hash(doc3_content),
        storage_path=f"storage/tenants/{tenant_id}/docs/Querella_Penal_Fraude_Garza.pdf",
        doc_type=DocumentClassification.ESCRITO_JUDICIAL,
        is_original=True,
        is_confidential=True,
        page_count=15,
        created_at=now - timedelta(days=10)
    )

    doc4_content = (
        "INSTRUMENTO NOTARIAL NÚMERO 48,219. PODER GENERAL PARA PLEITOS Y COBRANZAS, ACTOS DE ADMINISTRACIÓN Y DOMINIO. "
        "Otorgado por Operadora Logística del Norte S.A.P.I. de C.V. a favor del Lic. Roberto González Garza ante Notario Público No. 102 CDMX."
    )
    doc4 = Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case_mercantil.id,
        client_id=client_logistica.id,
        uploaded_by_id=senior_lawyer.id if senior_lawyer else default_actor_id,
        title="Poder Notarial General para Pleitos y Cobranzas Notaría 102",
        filename="Poder_Notarial_Logistica_2026.pdf",
        file_size_bytes=819200,
        mime_type="application/pdf",
        sha256_hash=make_hash(doc4_content),
        storage_path=f"storage/tenants/{tenant_id}/docs/Poder_Notarial_Logistica_2026.pdf",
        doc_type=DocumentClassification.PODER_NOTARIAL,
        is_original=True,
        is_confidential=False,
        page_count=6,
        created_at=now - timedelta(days=7)
    )

    doc5_content = (
        "CONTESTACIÓN DE DEMANDA EN JUICIO EJECUTIVO MERCANTIL ORAL. "
        "Expediente 215/2026. Se oponen excepciones de pago parcial y falta de legitimación pasiva sobre pagaré corporativo."
    )
    doc5 = Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case_mercantil.id,
        client_id=client_logistica.id,
        uploaded_by_id=senior_lawyer.id if senior_lawyer else default_actor_id,
        title="Contestación de Demanda y Excepciones Pagaré Mercantil",
        filename="Contestacion_Demanda_Mercantil_2026.docx",
        file_size_bytes=3145728,
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        sha256_hash=make_hash(doc5_content),
        storage_path=f"storage/tenants/{tenant_id}/docs/Contestacion_Demanda_Mercantil_2026.docx",
        doc_type=DocumentClassification.CONTESTACION,
        is_original=True,
        is_confidential=False,
        page_count=22,
        created_at=now - timedelta(days=4)
    )

    doc6_content = (
        "ACTA DE ASAMBLEA GENERAL EXTRAORDINARIA DE ACCIONISTAS DE INMOBILIARIA REFORMA CAPITAL S.A. DE C.V. "
        "Aumento de parte variable de capital social y designación de nuevo consejo de administración."
    )
    doc6 = Document(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        case_id=case_civil.id,
        client_id=client_inmobiliaria.id,
        uploaded_by_id=admin_lawyer.id if admin_lawyer else default_actor_id,
        title="Acta de Asamblea General Extraordinaria de Accionistas",
        filename="Acta_Asamblea_Reforma_Capital.pdf",
        file_size_bytes=614400,
        mime_type="application/pdf",
        sha256_hash=make_hash(doc6_content),
        storage_path=f"storage/tenants/{tenant_id}/docs/Acta_Asamblea_Reforma_Capital.pdf",
        doc_type=DocumentClassification.ACTA_ASAMBLEA,
        is_original=True,
        is_confidential=False,
        page_count=9,
        created_at=now - timedelta(days=1)
    )

    db.add_all([doc1, doc2, doc3, doc4, doc5, doc6])
    db.flush()

    # Metadatos extraídos de los documentos
    for d, text in [
        (doc1, doc1_content), (doc2, doc2_content), (doc3, doc3_content),
        (doc4, doc4_content), (doc5, doc5_content), (doc6, doc6_content)
    ]:
        meta = DocumentMetadata(
            document_id=d.id,
            parties=["Parte Actora", "Parte Demandada"],
            doc_date="2026-02-15",
            subject_matter=d.title,
            obligations=["Obligaciones de dar, hacer y no hacer"],
            amounts=[{"amount": 4850000.0, "currency": "MXN"}],
            terms_deadlines=["Plazo contractual: 36 meses"],
            signers=["Apoderado General", "Secretario del Consejo"],
            jurisdiction="Ciudad de México",
            court_authority="Poder Judicial de la CDMX",
            procedure_type="Vía Ordinaria",
            references=["Código Civil Federal", "Código de Comercio"],
            raw_text=text,
            ocr_applied=False,
            processing_time_ms=180
        )
        db.add(meta)

    # 5. Workflows y Asignaciones
    # Doc 1: APPROVED por Lic. Sofía Valenzuela
    wf1 = DocumentWorkflow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        document_id=doc1.id,
        current_state=WorkflowState.APPROVED,
        priority="HIGH",
        assigned_lawyer_id=senior_lawyer.id if senior_lawyer else None,
        reviewer_id=reviewer_lawyer.id if reviewer_lawyer else None,
        assigned_at=now - timedelta(days=18),
        created_at=now - timedelta(days=20)
    )
    # Aprobación formal registrada
    approval1 = WorkflowApprovalRecord(
        id=uuid.uuid4(),
        workflow_id=wf1.id,
        document_id=doc1.id,
        user_id=senior_lawyer.id if senior_lawyer else default_actor_id,
        user_name=senior_lawyer.full_name if senior_lawyer else "Lic. Sofía Valenzuela",
        user_role="SENIOR_LAWYER",
        version_number=1,
        document_hash=doc1.sha256_hash,
        scope=ApprovalScope.DEFINITIVE_APPROVAL,
        reviewer_license="98765432",
        approval_notes="Visto bueno definitivo emitido tras cotejo de cláusula penal y jurisdicción de la CDMX.",
        status="VALID",
        approved_at=now - timedelta(days=12)
    )

    # Doc 2: PENDING_REVIEW asignado a Lic. Roberto González Garza
    wf2 = DocumentWorkflow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        document_id=doc2.id,
        current_state=WorkflowState.PENDING_REVIEW,
        priority="MEDIUM",
        assigned_lawyer_id=admin_lawyer.id if admin_lawyer else None,
        reviewer_id=reviewer_lawyer.id if reviewer_lawyer else None,
        assigned_at=now - timedelta(days=12),
        deadline_at=now + timedelta(days=3),
        created_at=now - timedelta(days=14)
    )

    # Doc 3: WITH_OBSERVATIONS asignado a Lic. Carlos Mendoza Silva
    wf3 = DocumentWorkflow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        document_id=doc3.id,
        current_state=WorkflowState.WITH_OBSERVATIONS,
        priority="URGENT",
        assigned_lawyer_id=reviewer_lawyer.id if reviewer_lawyer else None,
        assigned_at=now - timedelta(days=8),
        deadline_at=now + timedelta(days=1),
        created_at=now - timedelta(days=10)
    )

    # Doc 4: PENDING_APPROVAL asignado a Lic. Sofía Valenzuela
    wf4 = DocumentWorkflow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        document_id=doc4.id,
        current_state=WorkflowState.PENDING_APPROVAL,
        priority="HIGH",
        assigned_lawyer_id=senior_lawyer.id if senior_lawyer else None,
        reviewer_id=reviewer_lawyer.id if reviewer_lawyer else None,
        assigned_at=now - timedelta(days=5),
        deadline_at=now + timedelta(days=4),
        created_at=now - timedelta(days=7)
    )

    # Doc 5: PROCESSING
    wf5 = DocumentWorkflow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        document_id=doc5.id,
        current_state=WorkflowState.PROCESSING,
        priority="MEDIUM",
        assigned_lawyer_id=senior_lawyer.id if senior_lawyer else None,
        assistant_id=assistant_user.id if assistant_user else None,
        assigned_at=now - timedelta(days=3),
        created_at=now - timedelta(days=4)
    )

    # Doc 6: RECEIVED
    wf6 = DocumentWorkflow(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        document_id=doc6.id,
        current_state=WorkflowState.RECEIVED,
        priority="LOW",
        created_at=now - timedelta(days=1)
    )

    db.add_all([wf1, approval1, wf2, wf3, wf4, wf5, wf6])
    db.flush()

    # 6. Riesgos y Hallazgos Jurídicos (LegalFindings)
    session1 = AdvancedAnalysisSession(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        document_id=doc1.id,
        created_by_id=senior_lawyer.id if senior_lawyer else default_actor_id,
        overall_risk_score=78.5,
        overall_severity=FindingSeverity.CRITICAL,
        findings_count=1,
        critical_count=1,
        high_count=0,
        medium_count=0,
        low_count=0,
        pending_review_count=0,
        summary="Detección de pena convencional excesiva en arrendamiento comercial que excede el límite del Código Civil Federal.",
        execution_time_ms=420,
        created_at=now - timedelta(days=12)
    )

    session2 = AdvancedAnalysisSession(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        document_id=doc5.id,
        created_by_id=senior_lawyer.id if senior_lawyer else default_actor_id,
        overall_risk_score=52.0,
        overall_severity=FindingSeverity.HIGH,
        findings_count=1,
        critical_count=0,
        high_count=1,
        medium_count=0,
        low_count=0,
        pending_review_count=1,
        summary="Identificación de cláusula de jurisdicción y competencia difusa en excepciones mercantiles.",
        execution_time_ms=390,
        created_at=now - timedelta(days=3)
    )

    db.add_all([session1, session2])
    db.flush()

    finding_crit = LegalFinding(
        id=uuid.uuid4(),
        session_id=session1.id,
        tenant_id=tenant_id,
        document_id=doc1.id,
        finding_code="FIND-CRIT-001",
        title="Cláusula penal que excede el valor principal del contrato",
        description="La cláusula penal estipula un pago equivalente al 100% adicional sobre el valor total, lo que transgrede la prohibición expresa del Código Civil Federal.",
        original_fragment="CLÁUSULA DÉCIMA CUARTA. En caso de incumplimiento, el arrendatario pagará una pena de 100% del valor total del contrato...",
        clause_ref="Décima Cuarta",
        location="Página 6, Párrafo 2",
        issue_type="EXCESO_PUNITIVO",
        severity=FindingSeverity.CRITICAL,
        risk_explanation="Nulidad parcial de la cláusula en juicio ordinario mercantil o civil y pérdida de certeza en la indemnización pactada.",
        recommendation="Ajustar la pena convencional a un porcentaje proporcional (no mayor al 20% del monto devengado) conforme al artículo 1843 del Código Civil Federal.",
        review_status=FindingReviewStatus.VALIDATED,
        reviewer_notes="Validado por Lic. Sofía Valenzuela. Propuesta de sustitución redactada en versión 2.",
        reviewer_license="98765432",
        reviewed_by_id=senior_lawyer.id if senior_lawyer else default_actor_id,
        reviewed_at=now - timedelta(days=12)
    )

    finding_high = LegalFinding(
        id=uuid.uuid4(),
        session_id=session2.id,
        tenant_id=tenant_id,
        document_id=doc5.id,
        finding_code="FIND-HIGH-002",
        title="Ambigüedad en sumisión de fueros concurrentes",
        description="Falta de renuncia expresa al fuero por razón de domicilio presente o futuro en pagaré corporativo.",
        original_fragment="Las partes podrán acudir a las autoridades de su elección para el cobro del título...",
        clause_ref="Cláusula de Competencia",
        location="Página 18, Párrafo 4",
        issue_type="COMPETENCIA_PROCESAL",
        severity=FindingSeverity.HIGH,
        risk_explanation="Riesgo de excepción de incompetencia por declinatoria en juzgado de distrito.",
        recommendation="Especificar con exactitud los juzgados mercantiles de la Ciudad de México o Monterrey conforme al artículo 1093 del Código de Comercio.",
        review_status=FindingReviewStatus.PENDING_REVIEW
    )

    db.add_all([finding_crit, finding_high])

    # 7. Transiciones de Workflow para el historial de actividad reciente
    trans1 = WorkflowTransition(
        id=uuid.uuid4(),
        workflow_id=wf1.id,
        from_state=WorkflowState.PENDING_REVIEW,
        to_state=WorkflowState.APPROVED,
        triggered_by_id=senior_lawyer.id if senior_lawyer else default_actor_id,
        reason="Aprobación formal definitiva emitida con Cédula Profesional 98765432.",
        created_at=now - timedelta(hours=3)
    )
    trans2 = WorkflowTransition(
        id=uuid.uuid4(),
        workflow_id=wf4.id,
        from_state=WorkflowState.WITH_OBSERVATIONS,
        to_state=WorkflowState.PENDING_APPROVAL,
        triggered_by_id=reviewer_lawyer.id if reviewer_lawyer else default_actor_id,
        reason="Observaciones de poderes notariales solventadas por el apoderado legal.",
        created_at=now - timedelta(hours=7)
    )
    trans3 = WorkflowTransition(
        id=uuid.uuid4(),
        workflow_id=wf3.id,
        from_state=WorkflowState.PROCESSING,
        to_state=WorkflowState.WITH_OBSERVATIONS,
        triggered_by_id=reviewer_lawyer.id if reviewer_lawyer else default_actor_id,
        reason="Detección de incongruencia en fechas de hechos de la querella penal.",
        created_at=now - timedelta(hours=14)
    )
    trans4 = WorkflowTransition(
        id=uuid.uuid4(),
        workflow_id=wf2.id,
        from_state=WorkflowState.RECEIVED,
        to_state=WorkflowState.PENDING_REVIEW,
        triggered_by_id=admin_lawyer.id if admin_lawyer else default_actor_id,
        reason="Expediente familiar radicado y asignado a revisión de convenio.",
        created_at=now - timedelta(days=1)
    )

    db.add_all([trans1, trans2, trans3, trans4])

    # 8. Entradas de Bitácora Forense (AuditLog)
    audit1 = AuditLog(
        tenant_id=tenant_id,
        user_id=senior_lawyer.id if senior_lawyer else default_actor_id,
        action="APPROVAL_ISSUED",
        resource_type="WORKFLOW_APPROVAL",
        resource_id=str(approval1.id),
        details={"doc_title": doc1.title, "scope": "DEFINITIVE_APPROVAL", "license": "98765432"},
        created_at=now - timedelta(hours=3)
    )
    audit2 = AuditLog(
        tenant_id=tenant_id,
        user_id=reviewer_lawyer.id if reviewer_lawyer else default_actor_id,
        action="ANALYSIS_VALIDATION",
        resource_type="LEGAL_FINDING",
        resource_id=str(finding_crit.id),
        details={"code": "FIND-CRIT-001", "decision": "VALIDATED"},
        created_at=now - timedelta(hours=8)
    )
    audit3 = AuditLog(
        tenant_id=tenant_id,
        user_id=admin_lawyer.id if admin_lawyer else default_actor_id,
        action="CASE_CREATION",
        resource_type="CASE",
        resource_id=str(case_civil.id),
        details={"case_number": case_civil.case_number, "matter": "CIVIL"},
        created_at=now - timedelta(days=25)
    )

    db.add_all([audit1, audit2, audit3])
    db.commit()

    logger.info("Datos de demostración sembrados exitosamente: 4 clientes, 4 expedientes, 6 documentos, workflows y auditoría.")
