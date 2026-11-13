from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.workflow import (
    DocumentWorkflow, WorkflowApprovalRecord, WorkflowState,
    ApprovalScope, WorkflowTransition
)
from app.models.document import Document
from app.models.user import User
from app.core.errors import ValidationException, ForbiddenException, NotFoundException
from app.core.logging import logger


class ApprovalService:
    """Gestiona el ciclo de aprobaciones humanas, reglas de competencia e invalidación automática."""

    def __init__(self, db: Session):
        self.db = db

    def submit_approval(
        self,
        workflow: DocumentWorkflow,
        user: User,
        scope: str = ApprovalScope.DEFINITIVE_APPROVAL,
        reviewer_license: Optional[str] = None,
        notes: Optional[str] = None
    ) -> WorkflowApprovalRecord:
        """
        Emite una aprobación legal verificando competencia y registrando alcance, versión y hash.
        """
        # 1. Regla: La IA no puede aprobar documentos
        if not getattr(user, "id", None) or getattr(user, "role", None) in ["AI", "SYSTEM", "BOT"]:
            raise ValidationException("La IA no tiene personalidad jurídica para aprobar documentos legales.")

        # 2. Regla: Restricción para asistentes jurídicos
        effective_license = reviewer_license or getattr(user, "professional_license", None)
        if user.role in ["LEGAL_ASSISTANT", "ASSISTANT"]:
            if scope == ApprovalScope.DEFINITIVE_APPROVAL and not workflow.allow_assistant_approval:
                raise ForbiddenException(
                    "Los asistentes jurídicos no están facultados para emitir aprobaciones definitivas "
                    "salvo autorización expresa del titular o socio del despacho."
                )

        # 3. Regla: Para aprobación definitiva, se requiere abogado facultado y cédula profesional
        if scope == ApprovalScope.DEFINITIVE_APPROVAL:
            authorized_roles = ["MANAGING_PARTNER", "SENIOR_LAWYER", "ASSOCIATE_LAWYER"]
            if user.role not in authorized_roles and not workflow.allow_assistant_approval:
                raise ForbiddenException(
                    f"El rol '{user.role}' no cuenta con facultades para emitir aprobaciones definitivas."
                )
            if not effective_license or len(effective_license.strip()) < 4:
                raise ValidationException(
                    "Es obligatorio registrar la Cédula Profesional del abogado que emite la aprobación definitiva."
                )

        # 4. Obtener documento y versión actual
        doc = self.db.query(Document).filter(Document.id == workflow.document_id).first()
        if not doc:
            raise NotFoundException("Documento no encontrado para emitir aprobación.")

        current_version_number = len(doc.versions) if doc.versions else 1
        current_hash = doc.sha256_hash

        # 5. Crear registro formal de aprobación
        approval = WorkflowApprovalRecord(
            workflow_id=workflow.id,
            document_id=doc.id,
            user_id=user.id,
            user_name=user.full_name,
            user_role=user.role,
            version_number=current_version_number,
            document_hash=current_hash,
            scope=scope,
            status="VALID",
            reviewer_license=effective_license.strip() if effective_license else None,
            approval_notes=notes.strip() if notes else None,
            approved_at=datetime.now(timezone.utc)
        )
        self.db.add(approval)

        # 6. Si es aprobación definitiva, promover el workflow a APPROVED
        if scope == ApprovalScope.DEFINITIVE_APPROVAL:
            from_state = workflow.current_state
            workflow.current_state = WorkflowState.APPROVED
            workflow.updated_at = datetime.now(timezone.utc)

            transition = WorkflowTransition(
                workflow_id=workflow.id,
                from_state=from_state,
                to_state=WorkflowState.APPROVED,
                triggered_by_id=user.id,
                trigger_type="USER_ACTION",
                reason=f"Aprobación definitiva otorgada por Lic. {user.full_name} (Cédula: {effective_license}) sobre v{current_version_number}",
                transition_metadata={
                    "scope": scope,
                    "version_number": current_version_number,
                    "document_hash": current_hash,
                    "license": effective_license
                }
            )
            self.db.add(transition)

        self.db.flush()
        logger.info(
            f"[ApprovalService] Aprobación {scope} registrada para Doc:{doc.id} v{current_version_number} "
            f"por Lic. {user.full_name} ({effective_license})"
        )

        return approval

    def invalidate_approvals_on_change(
        self,
        document_id: UUID,
        new_version_number: int,
        reason: str
    ) -> List[WorkflowApprovalRecord]:
        """
        Regla crítica: Los cambios posteriores a una aprobación invalidan automáticamente
        dicha aprobación cuando afecten el contenido aprobado.
        """
        valid_approvals = self.db.query(WorkflowApprovalRecord).filter(
            WorkflowApprovalRecord.document_id == document_id,
            WorkflowApprovalRecord.status == "VALID",
            WorkflowApprovalRecord.version_number < new_version_number
        ).all()

        invalidated_list = []
        now = datetime.now(timezone.utc)

        for app in valid_approvals:
            app.status = "INVALIDATED_BY_CONTENT_CHANGE"
            app.invalidated_at = now
            app.invalidated_by_version = new_version_number
            app.invalidation_reason = reason
            invalidated_list.append(app)

        # Si el flujo estaba en APROBADO, regresar el workflow a EN CORRECCIÓN / REVISIÓN
        workflow = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.document_id == document_id
        ).first()

        if workflow and workflow.current_state == WorkflowState.APPROVED:
            from_state = workflow.current_state
            workflow.current_state = WorkflowState.IN_CORRECTION
            workflow.updated_at = now

            transition = WorkflowTransition(
                workflow_id=workflow.id,
                from_state=from_state,
                to_state=WorkflowState.IN_CORRECTION,
                triggered_by_id=None,
                trigger_type="SYSTEM_AUTOMATION",
                reason=f"Aprobación invalidada automáticamente al crearse la versión {new_version_number}: {reason}",
                transition_metadata={
                    "invalidated_approvals_count": len(invalidated_list),
                    "new_version_number": new_version_number
                }
            )
            self.db.add(transition)

        self.db.flush()
        logger.warning(
            f"[ApprovalService] Invalidadas {len(invalidated_list)} aprobaciones previas en Doc:{document_id} "
            f"debido a nueva versión {new_version_number}"
        )

        return invalidated_list
