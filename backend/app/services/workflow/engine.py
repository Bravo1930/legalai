from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.workflow import (
    DocumentWorkflow, WorkflowState, WorkflowTransition,
    ApprovalScope, WorkflowApprovalRecord
)
from app.models.user import User
from app.models.document import Document
from app.core.errors import ValidationException, ForbiddenException, NotFoundException
from app.core.logging import logger


# Grafo configurable de transiciones permitidas
ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    WorkflowState.RECEIVED: [
        WorkflowState.PENDING_PROCESSING,
        WorkflowState.PROCESSING,
        WorkflowState.IN_CORRECTION,
        WorkflowState.ARCHIVED,
        WorkflowState.REJECTED
    ],
    WorkflowState.PENDING_PROCESSING: [
        WorkflowState.PROCESSING,
        WorkflowState.ARCHIVED,
        WorkflowState.REJECTED
    ],
    WorkflowState.PROCESSING: [
        WorkflowState.ANALYSIS_COMPLETED,
        WorkflowState.WITH_OBSERVATIONS,
        WorkflowState.PENDING_REVIEW,
        WorkflowState.REJECTED
    ],
    WorkflowState.ANALYSIS_COMPLETED: [
        WorkflowState.WITH_OBSERVATIONS,
        WorkflowState.PENDING_REVIEW,
        WorkflowState.PENDING_APPROVAL,
        WorkflowState.IN_CORRECTION,
        WorkflowState.ARCHIVED
    ],
    WorkflowState.WITH_OBSERVATIONS: [
        WorkflowState.IN_CORRECTION,
        WorkflowState.PENDING_REVIEW,
        WorkflowState.PENDING_APPROVAL,
        WorkflowState.REJECTED
    ],
    WorkflowState.PENDING_REVIEW: [
        WorkflowState.IN_CORRECTION,
        WorkflowState.PENDING_APPROVAL,
        WorkflowState.WITH_OBSERVATIONS,
        WorkflowState.REJECTED
    ],
    WorkflowState.IN_CORRECTION: [
        WorkflowState.PENDING_REVIEW,
        WorkflowState.PENDING_APPROVAL,
        WorkflowState.PROCESSING
    ],
    WorkflowState.PENDING_APPROVAL: [
        WorkflowState.APPROVED,
        WorkflowState.IN_CORRECTION,
        WorkflowState.REJECTED
    ],
    WorkflowState.APPROVED: [
        WorkflowState.ARCHIVED,
        WorkflowState.IN_CORRECTION  # Si un cambio posterior invalida la aprobación
    ],
    WorkflowState.REJECTED: [
        WorkflowState.IN_CORRECTION,
        WorkflowState.PENDING_REVIEW,
        WorkflowState.ARCHIVED
    ],
    WorkflowState.ARCHIVED: [
        WorkflowState.RECEIVED,
        WorkflowState.PENDING_PROCESSING
    ]
}


class WorkflowEngine:
    """Motor de workflow jurídico configurable con validación de guardas y reglas de negocio."""

    def __init__(self, db: Session):
        self.db = db

    def get_allowed_transitions(self, workflow: DocumentWorkflow, user: User) -> List[Dict[str, Any]]:
        """Calcula las transiciones disponibles para el estado actual considerando el rol del usuario."""
        current = workflow.current_state
        candidates = ALLOWED_TRANSITIONS.get(current, [])
        result = []

        for target in candidates:
            can_execute, reason = self._check_guard_permission(workflow, current, target, user)
            result.append({
                "target_state": target,
                "can_execute": can_execute,
                "block_reason": None if can_execute else reason,
                "requires_reason": target in [WorkflowState.REJECTED, WorkflowState.IN_CORRECTION],
                "requires_license": target == WorkflowState.APPROVED
            })

        return result

    def _check_guard_permission(
        self,
        workflow: DocumentWorkflow,
        from_state: str,
        to_state: str,
        user: User
    ) -> (bool, Optional[str]):
        """Valida si el usuario y el estado del documento cumplen los requisitos para la transición."""
        # 1. Validación de rol SUPER_ADMIN prohibido en documentos de despachos
        if user.role == "SUPER_ADMIN":
            return False, "Los administradores globales de plataforma no pueden gestionar flujos documentales privados."

        # 2. Regla fundamental: La IA no puede aprobar documentos ni ejecutar transiciones de aprobación
        if not getattr(user, "id", None) or getattr(user, "role", None) in ["AI", "SYSTEM", "BOT"]:
            return False, "La IA no tiene personalidad jurídica para ejecutar transiciones en el flujo legal."

        # 3. Transición a APROBADO
        if to_state == WorkflowState.APPROVED:
            # Los asistentes no pueden aprobar documentos definitivos salvo política expresa
            if user.role in ["LEGAL_ASSISTANT", "ASSISTANT"]:
                if not workflow.allow_assistant_approval:
                    return False, "Los asistentes jurídicos no pueden aprobar documentos definitivos sin política expresa."
            
            # Debe existir al menos un abogado responsable o el usuario debe ser abogado facultado
            lawyer_roles = ["MANAGING_PARTNER", "SENIOR_LAWYER", "ASSOCIATE_LAWYER"]
            if user.role not in lawyer_roles and not workflow.allow_assistant_approval:
                return False, "La aprobación definitiva requiere un abogado facultado con cédula profesional."

        # 4. Transición a PENDIENTE DE APROBACIÓN
        if to_state == WorkflowState.PENDING_APPROVAL:
            if not workflow.assigned_lawyer_id and user.role not in ["MANAGING_PARTNER", "SENIOR_LAWYER"]:
                return False, "Debe asignarse un abogado titular responsable antes de enviar a aprobación."

        return True, None

    def execute_transition(
        self,
        workflow: DocumentWorkflow,
        to_state: str,
        user: User,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        trigger_type: str = "USER_ACTION"
    ) -> DocumentWorkflow:
        """Aplica una transición validada, asienta la auditoría inmutable y actualiza el workflow."""
        from_state = workflow.current_state

        if to_state not in ALLOWED_TRANSITIONS.get(from_state, []):
            raise ValidationException(
                f"Transición no permitida de '{from_state}' a '{to_state}'. "
                f"Transiciones válidas: {ALLOWED_TRANSITIONS.get(from_state, [])}"
            )

        # Validar guardas
        can_exec, block_reason = self._check_guard_permission(workflow, from_state, to_state, user)
        if not can_exec:
            raise ForbiddenException(block_reason or "No tiene permisos para ejecutar esta transición.")

        # Requerimiento de justificación para rechazos o correcciones
        if to_state in [WorkflowState.REJECTED, WorkflowState.IN_CORRECTION] and (not reason or len(reason.strip()) < 3):
            raise ValidationException(f"La transición a '{to_state}' requiere ingresar una justificación detallada.")

        # Actualizar estado actual
        workflow.current_state = to_state
        workflow.updated_at = datetime.now(timezone.utc)

        # Asentar auditoría inmutable en workflow_transitions
        transition_record = WorkflowTransition(
            workflow_id=workflow.id,
            from_state=from_state,
            to_state=to_state,
            triggered_by_id=user.id if hasattr(user, "id") else None,
            trigger_type=trigger_type,
            reason=reason.strip() if reason else None,
            transition_metadata=metadata or {}
        )
        self.db.add(transition_record)
        self.db.flush()

        logger.info(
            f"[WorkflowEngine] Transición ejecutada para Doc:{workflow.document_id} "
            f"'{from_state}' -> '{to_state}' por Usuario:{getattr(user, 'email', 'SYS')}"
        )

        return workflow
