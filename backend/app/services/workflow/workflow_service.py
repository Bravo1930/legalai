from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.workflow import (
    DocumentWorkflow, WorkflowTransition, WorkflowComment,
    CorrectionRequest, WorkflowApprovalRecord, WorkflowReminder,
    WorkflowNotification, WorkflowState, ApprovalScope
)
from app.models.document import Document
from app.models.user import User
from app.core.errors import ValidationException, ForbiddenException, NotFoundException
from app.core.logging import logger
from app.services.workflow.engine import WorkflowEngine
from app.services.workflow.approval_service import ApprovalService
from app.services.workflow.notification_service import NotificationService, NotificationType


class WorkflowService:
    """Orquestador central del ciclo de vida y flujos de trabajo jurídicos."""

    def __init__(self, db: Session):
        self.db = db
        self.engine = WorkflowEngine(db)
        self.approval_service = ApprovalService(db)
        self.notification_service = NotificationService(db)

    def _verify_tenant_access(self, tenant_id: UUID, user: User, document: Optional[Document] = None):
        """Verifica el aislamiento multi-inquilino y bloquea al SUPER_ADMIN sobre documentos privados."""
        if user.role == "SUPER_ADMIN":
            raise ForbiddenException("Los administradores globales no tienen acceso a expedientes jurídicos privados.")
        if user.tenant_id != tenant_id:
            raise ForbiddenException("No tiene autorización para operar sobre este despacho jurídico.")
        if document and document.tenant_id != tenant_id:
            raise ForbiddenException("El documento especificado no pertenece a este despacho.")

    def get_or_create_workflow(
        self,
        tenant_id: UUID,
        user: User,
        document_id: UUID
    ) -> DocumentWorkflow:
        """Obtiene el workflow existente o inicializa uno nuevo en estado RECIBIDO."""
        self._verify_tenant_access(tenant_id, user)

        doc = self.db.query(Document).filter(
            Document.id == document_id,
            Document.tenant_id == tenant_id
        ).first()

        if not doc:
            raise NotFoundException("Documento no encontrado en este despacho.")

        wf = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.document_id == document_id,
            DocumentWorkflow.tenant_id == tenant_id
        ).first()

        if not wf:
            wf = DocumentWorkflow(
                tenant_id=tenant_id,
                document_id=document_id,
                current_state=WorkflowState.RECEIVED,
                priority="MEDIUM",
                allow_assistant_approval=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            self.db.add(wf)
            self.db.flush()

            # Transición inicial de auditoría
            init_transition = WorkflowTransition(
                workflow_id=wf.id,
                from_state="NONE",
                to_state=WorkflowState.RECEIVED,
                triggered_by_id=user.id if hasattr(user, "id") else None,
                trigger_type="SYSTEM_AUTOMATION",
                reason="Recepción e incorporación del documento al sistema de flujos jurídicos.",
                transition_metadata={"initial": True}
            )
            self.db.add(init_transition)
            self.db.commit()

        # Revisar si el plazo fatal venció
        if wf.deadline_at and wf.deadline_at < datetime.now(timezone.utc) and not wf.is_overdue:
            wf.is_overdue = True
            self.db.commit()

        return wf

    def assign_team(
        self,
        tenant_id: UUID,
        user: User,
        workflow_id: UUID,
        lawyer_id: Optional[UUID] = None,
        reviewer_id: Optional[UUID] = None,
        assistant_id: Optional[UUID] = None,
        deadline_at: Optional[datetime] = None,
        priority: Optional[str] = None,
        allow_assistant_approval: Optional[bool] = None
    ) -> DocumentWorkflow:
        """Asigna o reasigna abogados responsables, revisores, asistentes y plazos límite."""
        wf = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.id == workflow_id,
            DocumentWorkflow.tenant_id == tenant_id
        ).first()

        if not wf:
            raise NotFoundException("Flujo de trabajo no encontrado.")

        self._verify_tenant_access(tenant_id, user)

        # Regla: Reasignación autorizada (Solo socios o abogados pueden asignar equipos)
        authorized_roles = ["MANAGING_PARTNER", "SENIOR_LAWYER", "ASSOCIATE_LAWYER"]
        if user.role not in authorized_roles:
            raise ForbiddenException("Solo los abogados o socios pueden asignar o modificar equipos de trabajo.")

        changes = []
        now = datetime.now(timezone.utc)

        if lawyer_id is not None and lawyer_id != wf.assigned_lawyer_id:
            wf.assigned_lawyer_id = lawyer_id
            changes.append("Abogado Responsable")
            # Notificar al abogado asignado
            self.notification_service.emit_notification(
                tenant_id=tenant_id,
                recipient_id=lawyer_id,
                notification_type=NotificationType.NEW_DOCUMENT_RECEIVED,
                title="📁 Documento Asignado para Conducción Jurídica",
                message=f"Se le ha asignado como abogado titular del documento.",
                document_id=wf.document_id
            )

        if reviewer_id is not None and reviewer_id != wf.reviewer_id:
            wf.reviewer_id = reviewer_id
            changes.append("Revisor Jurídico")
            self.notification_service.emit_notification(
                tenant_id=tenant_id,
                recipient_id=reviewer_id,
                notification_type=NotificationType.PENDING_REVIEW_ALERT,
                title="🔍 Designación como Revisor Jurídico",
                message=f"Ha sido asignado para revisar el documento.",
                document_id=wf.document_id
            )

        if assistant_id is not None and assistant_id != wf.assistant_id:
            wf.assistant_id = assistant_id
            changes.append("Asistente Jurídico")
            self.notification_service.emit_notification(
                tenant_id=tenant_id,
                recipient_id=assistant_id,
                notification_type=NotificationType.NEW_DOCUMENT_RECEIVED,
                title="📋 Asignación de Soporte Jurídico",
                message=f"Ha sido asignado como asistente para soporte del expediente.",
                document_id=wf.document_id
            )

        if deadline_at is not None:
            wf.deadline_at = deadline_at
            wf.is_overdue = deadline_at < now
            changes.append("Fecha Límite Fatal")

        if priority is not None:
            wf.priority = priority
            changes.append(f"Prioridad: {priority}")

        if allow_assistant_approval is not None:
            wf.allow_assistant_approval = allow_assistant_approval
            changes.append(f"Política Aprobación Asistente: {allow_assistant_approval}")

        wf.assigned_by_id = user.id
        wf.assigned_at = now
        wf.updated_at = now

        # Registrar transición interna de auditoría para la reasignación
        if changes:
            transition = WorkflowTransition(
                workflow_id=wf.id,
                from_state=wf.current_state,
                to_state=wf.current_state,
                triggered_by_id=user.id,
                trigger_type="USER_ACTION",
                reason=f"Actualización de asignación y gobernanza: {', '.join(changes)}.",
                transition_metadata={"changes": changes}
            )
            self.db.add(transition)

        self.db.commit()
        return wf

    def add_comment(
        self,
        tenant_id: UUID,
        user: User,
        workflow_id: UUID,
        comment_text: str,
        clause_reference: Optional[str] = None,
        is_internal_only: bool = True
    ) -> WorkflowComment:
        """Agrega un comentario o nota jurídica al expediente."""
        wf = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.id == workflow_id,
            DocumentWorkflow.tenant_id == tenant_id
        ).first()

        if not wf:
            raise NotFoundException("Flujo de trabajo no encontrado.")

        self._verify_tenant_access(tenant_id, user)

        if not comment_text or len(comment_text.strip()) < 2:
            raise ValidationException("El comentario no puede estar vacío.")

        comment = WorkflowComment(
            workflow_id=wf.id,
            author_id=user.id,
            author_name=user.full_name,
            author_role=user.role,
            comment_text=comment_text.strip(),
            clause_reference=clause_reference.strip() if clause_reference else None,
            is_internal_only=is_internal_only,
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(comment)

        # Notificar a los otros miembros del equipo
        self.notification_service.notify_team(
            workflow=wf,
            notification_type="WORKFLOW_COMMENT_ADDED",
            title="💬 Nuevo Comentario en Expediente",
            message=f"{user.full_name} ({user.role}): {comment_text[:80]}...",
            exclude_user_id=user.id
        )

        self.db.commit()
        return comment

    def request_correction(
        self,
        tenant_id: UUID,
        user: User,
        workflow_id: UUID,
        title: str,
        description: str,
        target_clause: Optional[str] = None,
        requested_to_id: Optional[UUID] = None
    ) -> CorrectionRequest:
        """Emite una solicitud de corrección formal y coloca el workflow en estado EN CORRECCIÓN."""
        wf = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.id == workflow_id,
            DocumentWorkflow.tenant_id == tenant_id
        ).first()

        if not wf:
            raise NotFoundException("Flujo de trabajo no encontrado.")

        self._verify_tenant_access(tenant_id, user)

        if not title or not description:
            raise ValidationException("El título y la descripción de la corrección son obligatorios.")

        # Determinar destinatario de la corrección
        target_recipient_id = requested_to_id or wf.assistant_id or wf.assigned_lawyer_id

        corr = CorrectionRequest(
            workflow_id=wf.id,
            requested_by_id=user.id,
            requested_to_id=target_recipient_id,
            title=title.strip(),
            description=description.strip(),
            target_clause=target_clause.strip() if target_clause else None,
            status="OPEN",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(corr)

        # Transicionar automáticamente a IN_CORRECTION
        if wf.current_state != WorkflowState.IN_CORRECTION:
            self.engine.execute_transition(
                workflow=wf,
                to_state=WorkflowState.IN_CORRECTION,
                user=user,
                reason=f"Solicitud de corrección ingresada: '{title}'",
                trigger_type="USER_ACTION"
            )

        # Notificar al destinatario
        if target_recipient_id:
            self.notification_service.emit_notification(
                tenant_id=tenant_id,
                recipient_id=target_recipient_id,
                notification_type=NotificationType.CORRECTION_REQUESTED,
                title="📝 Solicitud de Corrección Jurídica",
                message=f"Se requiere corregir: '{title}' en {target_clause or 'el documento'}.",
                document_id=wf.document_id
            )

        self.db.commit()
        return corr

    def resolve_correction(
        self,
        tenant_id: UUID,
        user: User,
        correction_id: UUID,
        resolution_notes: str
    ) -> CorrectionRequest:
        """Marca una corrección como resuelta e informa al equipo."""
        corr = self.db.query(CorrectionRequest).filter(
            CorrectionRequest.id == correction_id
        ).first()

        if not corr:
            raise NotFoundException("Solicitud de corrección no encontrada.")

        wf = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.id == corr.workflow_id,
            DocumentWorkflow.tenant_id == tenant_id
        ).first()

        if not wf:
            raise NotFoundException("Flujo no coincide con el despacho.")

        self._verify_tenant_access(tenant_id, user)

        corr.status = "RESOLVED"
        corr.resolution_notes = resolution_notes.strip() if resolution_notes else "Corrección aplicada satisfactoriamente."
        corr.resolved_by_id = user.id
        corr.resolved_at = datetime.now(timezone.utc)

        # Si ya no quedan correcciones abiertas, permitir volver a PENDING_REVIEW
        open_corrections = self.db.query(CorrectionRequest).filter(
            CorrectionRequest.workflow_id == wf.id,
            CorrectionRequest.status == "OPEN",
            CorrectionRequest.id != corr.id
        ).count()

        if open_corrections == 0 and wf.current_state == WorkflowState.IN_CORRECTION:
            self.engine.execute_transition(
                workflow=wf,
                to_state=WorkflowState.PENDING_REVIEW,
                user=user,
                reason="Todas las correcciones solicitadas han sido atendidas.",
                trigger_type="USER_ACTION"
            )

        self.db.commit()
        return corr

    def execute_transition(
        self,
        tenant_id: UUID,
        user: User,
        workflow_id: UUID,
        target_state: str,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentWorkflow:
        """Ejecuta una transición validada a través del WorkflowEngine."""
        wf = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.id == workflow_id,
            DocumentWorkflow.tenant_id == tenant_id
        ).first()

        if not wf:
            raise NotFoundException("Flujo de trabajo no encontrado.")

        self._verify_tenant_access(tenant_id, user)

        updated_wf = self.engine.execute_transition(
            workflow=wf,
            to_state=target_state,
            user=user,
            reason=reason,
            metadata=metadata
        )

        # Disparar alertas temáticas
        if target_state == WorkflowState.PENDING_REVIEW:
            self.notification_service.notify_team(
                workflow=wf,
                notification_type=NotificationType.PENDING_REVIEW_ALERT,
                title="🔍 Documento Listo para Revisión",
                message=f"El documento ha pasado al estado 'Pendiente de revisión'.",
                exclude_user_id=user.id
            )
        elif target_state == WorkflowState.PENDING_APPROVAL:
            self.notification_service.notify_team(
                workflow=wf,
                notification_type=NotificationType.PENDING_APPROVAL_ALERT,
                title="⚖️ Aprobación Requerida",
                message=f"El documento está listo y espera aprobación jurídica formal.",
                exclude_user_id=user.id
            )

        self.db.commit()
        return updated_wf

    def submit_approval(
        self,
        tenant_id: UUID,
        user: User,
        workflow_id: UUID,
        scope: str = ApprovalScope.DEFINITIVE_APPROVAL,
        reviewer_license: Optional[str] = None,
        notes: Optional[str] = None
    ) -> WorkflowApprovalRecord:
        """Aplica una aprobación formal e inscribe al documento en estado APROBADO."""
        wf = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.id == workflow_id,
            DocumentWorkflow.tenant_id == tenant_id
        ).first()

        if not wf:
            raise NotFoundException("Flujo de trabajo no encontrado.")

        self._verify_tenant_access(tenant_id, user)

        approval = self.approval_service.submit_approval(
            workflow=wf,
            user=user,
            scope=scope,
            reviewer_license=reviewer_license,
            notes=notes
        )

        # Notificar a todo el equipo
        self.notification_service.notify_team(
            workflow=wf,
            notification_type=NotificationType.APPROVAL_COMPLETED,
            title="✅ Documento Aprobado Formalmente",
            message=f"Aprobación otorgada por Lic. {user.full_name} ({scope}).",
            payload={"version_number": approval.version_number, "scope": scope}
        )

        self.db.commit()
        return approval

    def get_workflow_detail(
        self,
        tenant_id: UUID,
        user: User,
        workflow_id: UUID
    ) -> DocumentWorkflow:
        """Consulta el expediente completo de workflow con sus relaciones."""
        wf = self.db.query(DocumentWorkflow).filter(
            DocumentWorkflow.id == workflow_id,
            DocumentWorkflow.tenant_id == tenant_id
        ).first()

        if not wf:
            raise NotFoundException("Flujo no encontrado.")

        self._verify_tenant_access(tenant_id, user)
        return wf
