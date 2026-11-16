import os
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status

from app.models.rule import (
    LegalRule, RuleVersion, RuleAuditLog, RuleEvaluation,
    RuleEvaluationDetail, RuleEvaluationStatus
)
from app.models.document import Document
from app.models.user import User
from app.core.security import LegalRoles
from app.schemas.rule import LegalRuleCreate, LegalRuleUpdate, RuleVerificationRequest
from app.services.rules.rule_engine import DeterministicRuleEngine
from app.services.storage_service import StorageService


class RuleService:
    """Servicio empresarial para la gestión, versionado, auditoría y ejecución de reglas deterministas."""

    def __init__(self, db: Session):
        self.db = db
        self.engine = DeterministicRuleEngine()
        self.storage_service = StorageService()

    def create_rule(self, tenant_id: uuid.UUID, user_id: uuid.UUID, data: LegalRuleCreate) -> LegalRule:
        # Verificar unicidad de rule_code dentro del tenant
        existing = self.db.query(LegalRule).filter(
            LegalRule.tenant_id == tenant_id,
            LegalRule.rule_code == data.rule_code
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una regla con el código '{data.rule_code}' en su organización."
            )

        rule = LegalRule(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            rule_code=data.rule_code,
            name=data.name,
            description=data.description,
            category=data.category,
            severity=data.severity,
            is_active=True,
            scope=data.scope.model_dump(),
            condition_definition=data.condition_definition.model_dump(),
            expected_outcome=data.expected_outcome,
            legal_foundation=data.legal_foundation,
            version=1,
            effective_from=datetime.now(timezone.utc),
            effective_until=data.effective_until,
            created_by_id=user_id,
            responsible_lawyer_id=data.responsible_lawyer_id or user_id,
        )
        self.db.add(rule)
        self.db.flush()

        # Crear versión inicial (Versión 1)
        initial_version = RuleVersion(
            id=uuid.uuid4(),
            rule_id=rule.id,
            version_number=1,
            name=rule.name,
            description=rule.description,
            category=rule.category,
            severity=rule.severity,
            scope=rule.scope,
            condition_definition=rule.condition_definition,
            expected_outcome=rule.expected_outcome,
            legal_foundation=rule.legal_foundation,
            change_reason="Creación inicial de la regla",
            modified_by_id=user_id,
        )
        self.db.add(initial_version)

        # Registro de auditoría
        audit = RuleAuditLog(
            id=uuid.uuid4(),
            rule_id=rule.id,
            tenant_id=tenant_id,
            user_id=user_id,
            action="CREATE",
            diff_payload={"version": 1, "code": rule.rule_code, "name": rule.name}
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_rule(self, tenant_id: uuid.UUID, user_id: uuid.UUID, rule_id: uuid.UUID, data: LegalRuleUpdate) -> LegalRule:
        rule = self.db.query(LegalRule).filter(
            LegalRule.id == rule_id,
            LegalRule.tenant_id == tenant_id
        ).first()
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla no encontrada.")

        # Guardar snapshot de cambios
        changes = {}
        if data.name is not None and data.name != rule.name:
            changes["name"] = {"from": rule.name, "to": data.name}
            rule.name = data.name
        if data.description is not None and data.description != rule.description:
            changes["description"] = {"from": rule.description, "to": data.description}
            rule.description = data.description
        if data.category is not None and data.category != rule.category:
            changes["category"] = {"from": rule.category, "to": data.category}
            rule.category = data.category
        if data.severity is not None and data.severity != rule.severity:
            changes["severity"] = {"from": rule.severity, "to": data.severity}
            rule.severity = data.severity
        if data.scope is not None:
            new_scope = data.scope.model_dump()
            changes["scope"] = {"from": rule.scope, "to": new_scope}
            rule.scope = new_scope
        if data.condition_definition is not None:
            new_cond = data.condition_definition.model_dump()
            changes["condition_definition"] = {"from": rule.condition_definition, "to": new_cond}
            rule.condition_definition = new_cond
        if data.expected_outcome is not None:
            changes["expected_outcome"] = {"from": rule.expected_outcome, "to": data.expected_outcome}
            rule.expected_outcome = data.expected_outcome
        if data.legal_foundation is not None:
            changes["legal_foundation"] = {"from": rule.legal_foundation, "to": data.legal_foundation}
            rule.legal_foundation = data.legal_foundation
        if data.responsible_lawyer_id is not None:
            changes["responsible_lawyer_id"] = str(data.responsible_lawyer_id)
            rule.responsible_lawyer_id = data.responsible_lawyer_id
        if data.effective_until is not None:
            rule.effective_until = data.effective_until

        if not changes:
            return rule

        # Incrementar versión
        rule.version += 1
        rule.updated_at = datetime.now(timezone.utc)

        # Crear registro de versión inmutable
        new_version = RuleVersion(
            id=uuid.uuid4(),
            rule_id=rule.id,
            version_number=rule.version,
            name=rule.name,
            description=rule.description,
            category=rule.category,
            severity=rule.severity,
            scope=rule.scope,
            condition_definition=rule.condition_definition,
            expected_outcome=rule.expected_outcome,
            legal_foundation=rule.legal_foundation,
            change_reason=data.change_reason,
            modified_by_id=user_id,
        )
        self.db.add(new_version)

        # Auditoría
        audit = RuleAuditLog(
            id=uuid.uuid4(),
            rule_id=rule.id,
            tenant_id=tenant_id,
            user_id=user_id,
            action="UPDATE",
            diff_payload={"version": rule.version, "changes": changes, "reason": data.change_reason}
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def set_rule_status(self, tenant_id: uuid.UUID, user_id: uuid.UUID, rule_id: uuid.UUID, is_active: bool, reason: Optional[str] = None) -> LegalRule:
        rule = self.db.query(LegalRule).filter(
            LegalRule.id == rule_id,
            LegalRule.tenant_id == tenant_id
        ).first()
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla no encontrada.")

        rule.is_active = is_active
        rule.updated_at = datetime.now(timezone.utc)

        action = "ACTIVATE" if is_active else "DEACTIVATE"
        audit = RuleAuditLog(
            id=uuid.uuid4(),
            rule_id=rule.id,
            tenant_id=tenant_id,
            user_id=user_id,
            action=action,
            diff_payload={"is_active": is_active, "reason": reason}
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def list_rules(
        self,
        tenant_id: uuid.UUID,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[LegalRule]:
        q = self.db.query(LegalRule).filter(LegalRule.tenant_id == tenant_id)
        if category:
            q = q.filter(LegalRule.category == category)
        if severity:
            q = q.filter(LegalRule.severity == severity)
        if is_active is not None:
            q = q.filter(LegalRule.is_active == is_active)
        return q.order_by(LegalRule.rule_code.asc()).offset(skip).limit(limit).all()

    def get_rule(self, tenant_id: uuid.UUID, rule_id: uuid.UUID) -> LegalRule:
        rule = self.db.query(LegalRule).filter(
            LegalRule.id == rule_id,
            LegalRule.tenant_id == tenant_id
        ).first()
        if not rule:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla no encontrada.")
        return rule

    def evaluate_document_rules(
        self,
        tenant_id: uuid.UUID,
        user: User,
        document_id: uuid.UUID,
        rule_ids: Optional[List[uuid.UUID]] = None
    ) -> RuleEvaluation:
        # 1. El rol SUPER_ADMIN no puede auditar documentos confidenciales de despachos
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acceso restringido por diseño: El administrador global no puede inspeccionar documentos confidenciales de los despachos."
            )

        # 2. Obtener documento y validar aislamiento
        document = self.db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado o pertenece a otro despacho.")

        # 3. Leer texto extraído almacenado
        raw_text = ""
        if document.metadata_record and document.metadata_record.raw_text:
            raw_text = document.metadata_record.raw_text
        elif document.storage_path and os.path.exists(document.storage_path):
            try:
                with open(document.storage_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw_text = f.read()
            except Exception:
                pass

        # 4. Obtener reglas activas del despacho
        q = self.db.query(LegalRule).filter(
            LegalRule.tenant_id == tenant_id,
            LegalRule.is_active.is_(True)
        )
        if rule_ids:
            q = q.filter(LegalRule.id.in_(rule_ids))
        rules = q.all()

        if not rules:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay reglas deterministas activas configuradas para evaluar este documento."
            )

        # 5. Ejecutar evaluación determinista pura
        eval_result = self.engine.evaluate_document(
            document=document,
            raw_text=raw_text,
            rules=rules
        )

        # 6. Guardar evaluación en base de datos
        db_eval = RuleEvaluation(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            document_id=document.id,
            document_version_id=None,
            evaluated_by_id=user.id,
            total_rules_evaluated=eval_result["total_rules_evaluated"],
            passed_count=eval_result["passed_count"],
            failed_count=eval_result["failed_count"],
            pending_count=eval_result["pending_count"],
            not_applicable_count=eval_result["not_applicable_count"],
            compliance_score=eval_result["compliance_score"],
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(db_eval)
        self.db.flush()

        # Guardar detalles
        for item in eval_result["details"]:
            detail = RuleEvaluationDetail(
                id=uuid.uuid4(),
                evaluation_id=db_eval.id,
                rule_id=item["rule_id"],
                rule_code=item["rule_code"],
                rule_name=item["rule_name"],
                category=item["category"],
                severity=item["severity"],
                status=item["status"],
                matched_evidence=item.get("matched_evidence"),
                failure_reason=item.get("failure_reason")
            )
            self.db.add(detail)

        self.db.commit()
        self.db.refresh(db_eval)
        return db_eval

    def list_document_evaluations(self, tenant_id: uuid.UUID, user: User, document_id: uuid.UUID) -> List[RuleEvaluation]:
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido para SUPER_ADMIN.")

        # Verificar pertenencia del documento
        doc = self.db.query(Document).filter(Document.id == document_id, Document.tenant_id == tenant_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento no encontrado.")

        return self.db.query(RuleEvaluation).filter(
            RuleEvaluation.tenant_id == tenant_id,
            RuleEvaluation.document_id == document_id
        ).order_by(desc(RuleEvaluation.created_at)).all()

    def get_evaluation(self, tenant_id: uuid.UUID, user: User, evaluation_id: uuid.UUID) -> RuleEvaluation:
        if user.role == LegalRoles.SUPER_ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido para SUPER_ADMIN.")

        eval_rec = self.db.query(RuleEvaluation).filter(
            RuleEvaluation.id == evaluation_id,
            RuleEvaluation.tenant_id == tenant_id
        ).first()
        if not eval_rec:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluación no encontrada.")
        return eval_rec

    def verify_evaluation_detail(
        self,
        tenant_id: uuid.UUID,
        lawyer_user: User,
        detail_id: uuid.UUID,
        verification: RuleVerificationRequest
    ) -> RuleEvaluationDetail:
        """Permite que un abogado humano resuelva un dictamen en PENDING_HUMAN_REVIEW (HITL)."""
        if lawyer_user.role not in [LegalRoles.SENIOR_LAWYER, LegalRoles.LAWYER, LegalRoles.MANAGING_PARTNER, LegalRoles.ADMIN, LegalRoles.ASSOCIATE_LAWYER]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo un abogado o socio autorizado puede validar observaciones jurídicas."
            )

        detail = self.db.query(RuleEvaluationDetail).join(RuleEvaluation).filter(
            RuleEvaluationDetail.id == detail_id,
            RuleEvaluation.tenant_id == tenant_id
        ).first()
        if not detail:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Detalle de evaluación no encontrado.")

        # Validar nuevo estatus
        if verification.status not in [RuleEvaluationStatus.COMPLIANT, RuleEvaluationStatus.NON_COMPLIANT]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El estatus debe ser COMPLIANT o NON_COMPLIANT.")

        detail.status = verification.status
        detail.human_verification_notes = verification.notes
        detail.verified_by_id = lawyer_user.id
        detail.verified_at = datetime.now(timezone.utc)

        # Recalcular métricas de la evaluación padre
        eval_parent = detail.evaluation
        all_details = eval_parent.details
        passed = sum(1 for d in all_details if d.status == RuleEvaluationStatus.COMPLIANT)
        failed = sum(1 for d in all_details if d.status == RuleEvaluationStatus.NON_COMPLIANT)
        pending = sum(1 for d in all_details if d.status == RuleEvaluationStatus.PENDING_HUMAN_REVIEW)
        not_applicable = sum(1 for d in all_details if d.status == RuleEvaluationStatus.NOT_APPLICABLE)

        eval_parent.passed_count = passed
        eval_parent.failed_count = failed
        eval_parent.pending_count = pending
        eval_parent.not_applicable_count = not_applicable
        applicable_total = passed + failed + pending
        eval_parent.compliance_score = round((passed / applicable_total * 100), 2) if applicable_total > 0 else 100.0

        self.db.commit()
        self.db.refresh(detail)
        return detail
