import sys
import os
import uuid

# Asegurar path de backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.base import *
from app.db.session import SessionLocal
from app.core.logging import logger
from app.models.task import Task, TaskStatus
from app.workers.worker import process_task_logic
from app.services.task_service import TaskService


def run_database_cleanup(db: Session):
    logger.info("Iniciando saneamiento de base de datos y eliminación de duplicados...")

    demo_tenant = db.query(Tenant).filter(Tenant.slug == "despacho-demo").first()
    if not demo_tenant:
        logger.error("No se encontró despacho-demo")
        return

    tenant_id = demo_tenant.id

    # 1. Limpieza de usuarios de prueba generados por pytest
    logger.info("1. Depurando usuarios temporales de pruebas...")
    test_users = db.query(User).filter(
        (User.email.like("asistente_%@despacho.mx")) |
        (User.email.like("abogado_prueba_%@bufetemexico.demo")) |
        (User.email.like("abogado@despacho-b-%"))
    ).all()
    for u in test_users:
        db.delete(u)
    db.commit()

    # Eliminar despachos temporales de pruebas
    test_tenants = db.query(Tenant).filter(Tenant.slug.like("despacho-b-%")).all()
    for t in test_tenants:
        db.delete(t)
    db.commit()

    # 2. Limpieza de reglas de prueba (REG-TEST-% y REG-CONF-A-%)
    logger.info("2. Depurando reglas de prueba en catálogo...")
    test_rules = db.query(LegalRule).filter(
        (LegalRule.rule_code.like("REG-TEST-%")) |
        (LegalRule.rule_code.like("REG-CONF-A-%"))
    ).all()
    for r in test_rules:
        db.delete(r)
    db.commit()

    # Sembrar las 4 reglas maestras estándar si no existen
    admin_user = db.query(User).filter(User.email == "admin@legalai.mx").first()
    canonical_rules_defs = [
        {
            "rule_code": "REG-JUR-CDMX",
            "name": "Sometimiento Expreso a Tribunales de la Ciudad de México",
            "description": "Verifica que las controversias se sometan a los juzgados de la CDMX con renuncia a cualquier otro fuero.",
            "category": RuleCategory.JURISDICTION,
            "severity": RuleSeverity.CRITICAL,
            "scope": {"doc_types": ["*"]},
            "condition_definition": {
                "operator": RuleOperator.CONTAINS_ALL_KEYWORDS,
                "parameters": {"keywords": ["tribunales", "ciudad de méxico"]}
            },
            "expected_outcome": "Sometimiento formal y expreso a los tribunales de la CDMX.",
            "legal_foundation": "Art. 1093 del Código de Comercio"
        },
        {
            "rule_code": "REG-PROH-RENUNCIA",
            "name": "Prohibición de Renuncia a Prestaciones o Derechos Laborales",
            "description": "Detecta cláusulas ilícitas que pretendan eximir al patrón de indemnizaciones o finiquitos de ley.",
            "category": RuleCategory.PROHIBITED_CLAUSE,
            "severity": RuleSeverity.CRITICAL,
            "scope": {"doc_types": ["*"]},
            "condition_definition": {
                "operator": RuleOperator.PROHIBITS_KEYWORDS,
                "parameters": {"prohibited_keywords": ["renuncia irrevocable de prestaciones", "sin derecho a liquidación", "renuncia a derechos laborales"]}
            },
            "expected_outcome": "No contener renuncia a prestaciones mínimas constitucionales.",
            "legal_foundation": "Art. 33 de la Ley Federal del Trabajo y Art. 123 Constitucional"
        },
        {
            "rule_code": "REG-CONF-LFPPI",
            "name": "Cláusula de Confidencialidad y Secreto Industrial",
            "description": "Obligación contractual de guardar reserva absoluta sobre secretos comerciales y técnicos.",
            "category": RuleCategory.CONFIDENTIALITY,
            "severity": RuleSeverity.HIGH,
            "scope": {"doc_types": ["CONTRATO", "CONVENIO"]},
            "condition_definition": {
                "operator": RuleOperator.CONTAINS_ALL_KEYWORDS,
                "parameters": {"keywords": ["información confidencial", "secreto industrial"]}
            },
            "expected_outcome": "Pacto expreso de confidencialidad y protección de secretos industriales.",
            "legal_foundation": "Art. 82 y 85 de la Ley Federal de Protección a la Propiedad Industrial"
        },
        {
            "rule_code": "REG-DATOS-LFPDPPP",
            "name": "Cumplimiento de Protección de Datos Personales (LFPDPPP)",
            "description": "Verifica la existencia del aviso de privacidad y tratamiento de datos personales.",
            "category": RuleCategory.DATA_PROTECTION,
            "severity": RuleSeverity.HIGH,
            "scope": {"doc_types": ["*"]},
            "condition_definition": {
                "operator": RuleOperator.CONTAINS_ANY_KEYWORD,
                "parameters": {"keywords": ["aviso de privacidad", "datos personales", "lfpdppp"]}
            },
            "expected_outcome": "Referencia a aviso de privacidad conforme a la LFPDPPP.",
            "legal_foundation": "Ley Federal de Protección de Datos Personales en Posesión de los Particulares"
        }
    ]

    for r_def in canonical_rules_defs:
        existing_r = db.query(LegalRule).filter(
            LegalRule.tenant_id == tenant_id,
            LegalRule.rule_code == r_def["rule_code"]
        ).first()
        if not existing_r:
            new_r = LegalRule(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                rule_code=r_def["rule_code"],
                name=r_def["name"],
                description=r_def["description"],
                category=r_def["category"],
                severity=r_def["severity"],
                is_active=True,
                scope=r_def["scope"],
                condition_definition=r_def["condition_definition"],
                expected_outcome=r_def["expected_outcome"],
                legal_foundation=r_def["legal_foundation"],
                version=1,
                created_by_id=admin_user.id if admin_user else None
            )
            db.add(new_r)
    db.commit()

    # 3. Limpieza de expedientes de prueba (EXP-CONFIDENTIAL-%)
    logger.info("3. Depurando expedientes confidenciales temporales de pruebas...")
    test_cases = db.query(Case).filter(Case.case_number.like("EXP-CONFIDENTIAL-%")).all()
    for c in test_cases:
        db.delete(c)
    db.commit()

    # Asegurar que todos los expedientes válidos tengan status="ACTIVO" y state="CDMX"
    valid_cases = db.query(Case).all()
    for c in valid_cases:
        if not c.status:
            c.status = CaseStatus.ACTIVO
        if not c.state:
            c.state = "CDMX"
    db.commit()

    # 4. Deduplicación de Documentos
    logger.info("4. Deduplicando documentos en la bóveda inmutable...")
    # Agrupar por (tenant_id, sha256_hash)
    hash_groups = db.query(
        Document.tenant_id,
        Document.sha256_hash,
        func.count(Document.id)
    ).group_by(Document.tenant_id, Document.sha256_hash).having(func.count(Document.id) > 1).all()

    deleted_docs_count = 0
    for t_id, d_hash, _ in hash_groups:
        all_docs = db.query(Document).filter(
            Document.tenant_id == t_id,
            Document.sha256_hash == d_hash
        ).order_by(Document.created_at.asc()).all()

        # Seleccionar el primario: el que tenga workflow asociado o el primero
        primary_doc = all_docs[0]
        for candidate in all_docs:
            wf = db.query(DocumentWorkflow).filter(DocumentWorkflow.document_id == candidate.id).first()
            if wf:
                primary_doc = candidate
                break

        # Eliminar los duplicados
        for doc in all_docs:
            if doc.id != primary_doc.id:
                db.delete(doc)
                deleted_docs_count += 1

    db.commit()
    logger.info(f"Deduplicación de documentos completada. Se eliminaron {deleted_docs_count} copias duplicadas.")

    # 5. Corrección de AuditLog (testclient -> 127.0.0.1 y Lic. Lic. -> Lic.)
    logger.info("5. Corrigiendo registros de auditoría forense...")
    testclient_logs = db.query(AuditLog).filter(AuditLog.ip_address == "testclient").all()
    for log in testclient_logs:
        log.ip_address = "127.0.0.1"
    db.commit()

    # Corregir detalles con "Lic. Lic."
    all_logs = db.query(AuditLog).all()
    for log in all_logs:
        if log.details and isinstance(log.details, dict):
            fixed = False
            for k, v in list(log.details.items()):
                if isinstance(v, str) and "Lic. Lic." in v:
                    log.details[k] = v.replace("Lic. Lic.", "Lic.")
                    fixed = True
            if fixed:
                db.add(log)
    db.commit()

    # 6. Corrección de WorkflowApprovalRecord y WorkflowTransition ("Lic. Lic.")
    transitions = db.query(WorkflowTransition).all()
    for tr in transitions:
        if tr.reason and "Lic. Lic." in tr.reason:
            tr.reason = tr.reason.replace("Lic. Lic.", "Lic.")
    db.commit()

    approvals = db.query(WorkflowApprovalRecord).all()
    for ap in approvals:
        if ap.approval_notes and "Lic. Lic." in ap.approval_notes:
            ap.approval_notes = ap.approval_notes.replace("Lic. Lic.", "Lic.")
        if ap.user_name and "Lic. Lic." in ap.user_name:
            ap.user_name = ap.user_name.replace("Lic. Lic.", "Lic.")
    db.commit()

    # 7. Procesamiento de tareas pendientes atoradas en la Cola Asíncrona
    logger.info("7. Procesando tareas pendientes en la cola asíncrona...")
    pending_tasks = db.query(Task).filter(Task.status == TaskStatus.PENDING).all()
    logger.info(f"Se encontraron {len(pending_tasks)} tareas pendientes para procesar.")
    for task in pending_tasks:
        try:
            task.status = TaskStatus.PROCESSING
            db.commit()
            result = process_task_logic(task.task_type, task.payload or {})
            TaskService.update_task_status(db, task.id, TaskStatus.COMPLETED, result=result)
            logger.info(f"Tarea {task.id} ({task.task_type}) procesada exitosamente.")
        except Exception as ex:
            logger.error(f"Error procesando tarea {task.id}: {ex}")
            TaskService.update_task_status(db, task.id, TaskStatus.FAILED, error_message=str(ex))

    logger.info("Saneamiento de base de datos finalizado con éxito.")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        run_database_cleanup(db)
    finally:
        db.close()
