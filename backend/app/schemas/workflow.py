from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class WorkflowTransitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    from_state: str
    to_state: str
    triggered_by_id: Optional[UUID] = None
    trigger_type: str
    reason: Optional[str] = None
    transition_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class WorkflowCommentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    author_id: Optional[UUID] = None
    author_name: str
    author_role: str
    comment_text: str
    is_internal_only: bool
    clause_reference: Optional[str] = None
    created_at: datetime


class CreateWorkflowCommentRequest(BaseModel):
    comment_text: str = Field(..., min_length=2, description="Texto de la nota o comentario interno")
    clause_reference: Optional[str] = Field(None, description="Referencia a cláusula específica")
    is_internal_only: bool = Field(True, description="Si es visible solo para el equipo del despacho")


class CorrectionRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    requested_by_id: Optional[UUID] = None
    requested_to_id: Optional[UUID] = None
    title: str
    description: str
    target_clause: Optional[str] = None
    status: str
    resolution_notes: Optional[str] = None
    resolved_by_id: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime


class CreateCorrectionRequest(BaseModel):
    title: str = Field(..., min_length=3, description="Título del ajuste o corrección requerida")
    description: str = Field(..., min_length=5, description="Explicación detallada del cambio requerido")
    target_clause: Optional[str] = Field(None, description="Cláusula o sección afectada")
    requested_to_id: Optional[UUID] = Field(None, description="ID del usuario a quien se le asigna la corrección")


class ResolveCorrectionRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3, description="Explicación de cómo se solventó la corrección")


class WorkflowApprovalRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    document_id: UUID
    user_id: Optional[UUID] = None
    user_name: str
    user_role: str
    version_number: int
    document_hash: str
    scope: str
    status: str
    invalidation_reason: Optional[str] = None
    invalidated_at: Optional[datetime] = None
    invalidated_by_version: Optional[int] = None
    reviewer_license: Optional[str] = None
    approval_notes: Optional[str] = None
    approved_at: datetime


class SubmitApprovalRequest(BaseModel):
    scope: str = Field(default="DEFINITIVE_APPROVAL", description="DEFINITIVE_APPROVAL, LEGAL_CONTENT_APPROVAL, PRELIMINARY_APPROVAL")
    reviewer_license: Optional[str] = Field(None, description="Cédula profesional del abogado autorizador")
    notes: Optional[str] = Field(None, description="Dictamen u observaciones de la aprobación")


class WorkflowReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_id: UUID
    recipient_id: UUID
    remind_at: datetime
    message: str
    is_sent: bool
    sent_at: Optional[datetime] = None
    created_at: datetime


class CreateReminderRequest(BaseModel):
    remind_at: datetime = Field(..., description="Fecha y hora programada para el recordatorio")
    message: str = Field(..., min_length=3, description="Mensaje del recordatorio")
    recipient_id: Optional[UUID] = Field(None, description="ID del usuario destinatario (omita para sí mismo)")


class AllowedTransitionOption(BaseModel):
    target_state: str
    can_execute: bool
    block_reason: Optional[str] = None
    requires_reason: bool = False
    requires_license: bool = False


class WorkflowAssignTeamRequest(BaseModel):
    assigned_lawyer_id: Optional[UUID] = None
    reviewer_id: Optional[UUID] = None
    assistant_id: Optional[UUID] = None
    deadline_at: Optional[datetime] = None
    priority: Optional[str] = Field(None, description="LOW, MEDIUM, HIGH, URGENT")
    allow_assistant_approval: Optional[bool] = None


class WorkflowTransitionRequest(BaseModel):
    target_state: str = Field(..., description="Estado objetivo del flujo")
    reason: Optional[str] = Field(None, description="Motivo o justificación de la transición")
    metadata: Optional[Dict[str, Any]] = None


class DocumentWorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    document_id: UUID
    current_state: str
    priority: str
    assigned_lawyer_id: Optional[UUID] = None
    reviewer_id: Optional[UUID] = None
    assistant_id: Optional[UUID] = None
    assigned_by_id: Optional[UUID] = None
    assigned_at: Optional[datetime] = None
    deadline_at: Optional[datetime] = None
    is_overdue: bool
    allow_assistant_approval: bool
    created_at: datetime
    updated_at: datetime

    transitions: List[WorkflowTransitionResponse] = []
    comments: List[WorkflowCommentResponse] = []
    corrections: List[CorrectionRequestResponse] = []
    approvals: List[WorkflowApprovalRecordResponse] = []


class WorkflowNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    recipient_id: UUID
    document_id: Optional[UUID] = None
    notification_type: str
    title: str
    message: str
    payload: Optional[Dict[str, Any]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime
