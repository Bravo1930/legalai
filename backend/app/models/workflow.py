import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class WorkflowState:
    RECEIVED = "RECEIVED"                               # Recibido
    PENDING_PROCESSING = "PENDING_PROCESSING"           # Pendiente de procesamiento
    PROCESSING = "PROCESSING"                           # En procesamiento
    ANALYSIS_COMPLETED = "ANALYSIS_COMPLETED"           # Análisis completado
    WITH_OBSERVATIONS = "WITH_OBSERVATIONS"             # Con observaciones
    PENDING_REVIEW = "PENDING_REVIEW"                   # Pendiente de revisión
    IN_CORRECTION = "IN_CORRECTION"                     # En corrección
    PENDING_APPROVAL = "PENDING_APPROVAL"               # Pendiente de aprobación
    APPROVED = "APPROVED"                               # Aprobado
    REJECTED = "REJECTED"                               # Rechazado
    ARCHIVED = "ARCHIVED"                               # Archivado

    ALL_STATES = [
        RECEIVED, PENDING_PROCESSING, PROCESSING,
        ANALYSIS_COMPLETED, WITH_OBSERVATIONS, PENDING_REVIEW,
        IN_CORRECTION, PENDING_APPROVAL, APPROVED, REJECTED, ARCHIVED
    ]


class ApprovalScope:
    DEFINITIVE_APPROVAL = "DEFINITIVE_APPROVAL"         # Aprobación jurídica definitiva
    LEGAL_CONTENT_APPROVAL = "LEGAL_CONTENT_APPROVAL"   # Aprobación de cláusulas y contenido sustantivo
    PRELIMINARY_APPROVAL = "PRELIMINARY_APPROVAL"       # Aprobación preliminar / de formato
    TERMS_AND_CONDITIONS = "TERMS_AND_CONDITIONS"       # Aprobación de condiciones comerciales


class DocumentWorkflow(Base):
    """Representa el expediente de flujo de trabajo y estado del ciclo de vida del documento."""
    __tablename__ = "document_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    current_state = Column(String(50), nullable=False, default=WorkflowState.RECEIVED, index=True)
    priority = Column(String(20), nullable=False, default="MEDIUM")  # LOW, MEDIUM, HIGH, URGENT

    # Asignaciones del equipo legal
    assigned_lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assistant_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)

    # Fechas límites y SLA
    deadline_at = Column(DateTime(timezone=True), nullable=True, index=True)
    is_overdue = Column(Boolean, default=False, nullable=False)

    # Políticas del expediente
    allow_assistant_approval = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    tenant = relationship("Tenant")
    document = relationship("Document", foreign_keys=[document_id])
    assigned_lawyer = relationship("User", foreign_keys=[assigned_lawyer_id])
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    assistant = relationship("User", foreign_keys=[assistant_id])
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])

    transitions = relationship("WorkflowTransition", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowTransition.created_at.desc()")
    comments = relationship("WorkflowComment", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowComment.created_at.asc()")
    corrections = relationship("CorrectionRequest", back_populates="workflow", cascade="all, delete-orphan", order_by="CorrectionRequest.created_at.desc()")
    approvals = relationship("WorkflowApprovalRecord", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowApprovalRecord.approved_at.desc()")
    reminders = relationship("WorkflowReminder", back_populates="workflow", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<DocumentWorkflow Doc:{self.document_id} [{self.current_state}]>"


class WorkflowTransition(Base):
    """Historial inmutable de auditoría de cada transición de estado en el ciclo del documento."""
    __tablename__ = "workflow_transitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("document_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    
    from_state = Column(String(50), nullable=False)
    to_state = Column(String(50), nullable=False)
    triggered_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    trigger_type = Column(String(50), nullable=False, default="USER_ACTION")  # USER_ACTION, SYSTEM_AUTO, AI_HOOK
    reason = Column(Text, nullable=True)
    transition_metadata = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relaciones
    workflow = relationship("DocumentWorkflow", back_populates="transitions")
    triggered_by = relationship("User", foreign_keys=[triggered_by_id])

    def __repr__(self):
        return f"<WorkflowTransition {self.from_state} -> {self.to_state}>"


class WorkflowComment(Base):
    """Comentarios internos y notas de expediente entre los miembros del equipo jurídico."""
    __tablename__ = "workflow_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("document_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    author_name = Column(String(255), nullable=False)
    author_role = Column(String(50), nullable=False)
    comment_text = Column(Text, nullable=False)
    is_internal_only = Column(Boolean, default=True, nullable=False)
    clause_reference = Column(String(100), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relaciones
    workflow = relationship("DocumentWorkflow", back_populates="comments")
    author = relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<WorkflowComment by {self.author_name} ({self.author_role})>"


class CorrectionRequest(Base):
    """Solicitudes formales de corrección o ajuste jurídico solicitadas sobre un documento."""
    __tablename__ = "workflow_corrections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("document_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    requested_to_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    target_clause = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="OPEN")  # OPEN, IN_PROGRESS, RESOLVED, DISMISSED
    resolution_notes = Column(Text, nullable=True)
    resolved_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relaciones
    workflow = relationship("DocumentWorkflow", back_populates="corrections")
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    requested_to = relationship("User", foreign_keys=[requested_to_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])

    def __repr__(self):
        return f"<CorrectionRequest {self.title} [{self.status}]>"


class WorkflowApprovalRecord(Base):
    """
    Registro formal de aprobación jurídica con versión, alcance, cédula profesional
    e invalidación obligatoria si el contenido se modifica con posterioridad.
    """
    __tablename__ = "workflow_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("document_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user_name = Column(String(255), nullable=False)
    user_role = Column(String(50), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    document_hash = Column(String(64), nullable=False)  # Hash SHA-256 al momento de aprobar
    scope = Column(String(50), nullable=False, default=ApprovalScope.DEFINITIVE_APPROVAL)

    status = Column(String(50), nullable=False, default="VALID")  # VALID, INVALIDATED_BY_CONTENT_CHANGE, REVOKED
    invalidation_reason = Column(Text, nullable=True)
    invalidated_at = Column(DateTime(timezone=True), nullable=True)
    invalidated_by_version = Column(Integer, nullable=True)

    reviewer_license = Column(String(50), nullable=True)  # Cédula profesional
    approval_notes = Column(Text, nullable=True)
    approved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    workflow = relationship("DocumentWorkflow", back_populates="approvals")
    document = relationship("Document")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<WorkflowApprovalRecord v{self.version_number} [{self.status}] by {self.user_name}>"


class WorkflowReminder(Base):
    """Recordatorios programados de plazos fatales y revisiones de documentos."""
    __tablename__ = "workflow_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("document_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    remind_at = Column(DateTime(timezone=True), nullable=False, index=True)
    message = Column(Text, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    workflow = relationship("DocumentWorkflow", back_populates="reminders")
    recipient = relationship("User", foreign_keys=[recipient_id])


class WorkflowNotification(Base):
    """Centro de notificaciones dentro de la aplicación para el equipo legal."""
    __tablename__ = "workflow_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=True)

    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    payload = Column(JSON, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relaciones
    tenant = relationship("Tenant")
    recipient = relationship("User", foreign_keys=[recipient_id])
    document = relationship("Document")

    def __repr__(self):
        return f"<WorkflowNotification [{self.notification_type}] to User:{self.recipient_id}>"


class WorkflowIntegrationConfig(Base):
    """Configuración de integraciones externas (Webhooks, Slack, Teams, Email)."""
    __tablename__ = "workflow_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(255), nullable=True)
    slack_webhook_url = Column(String(500), nullable=True)
    teams_webhook_url = Column(String(500), nullable=True)

    notify_on_new_document = Column(Boolean, default=True, nullable=False)
    notify_on_critical_risk = Column(Boolean, default=True, nullable=False)
    notify_on_approval_needed = Column(Boolean, default=True, nullable=False)
    notify_on_correction = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    tenant = relationship("Tenant")
