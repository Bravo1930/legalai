from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.models.workflow import WorkflowApprovalRecord, DocumentWorkflow
from app.schemas.workflow import (
    DocumentWorkflowResponse,
    WorkflowTransitionResponse,
    WorkflowCommentResponse,
    CreateWorkflowCommentRequest,
    CorrectionRequestResponse,
    CreateCorrectionRequest,
    ResolveCorrectionRequest,
    WorkflowApprovalRecordResponse,
    SubmitApprovalRequest,
    WorkflowAssignTeamRequest,
    WorkflowTransitionRequest,
    AllowedTransitionOption,
    WorkflowNotificationResponse
)
from app.services.auth_service import get_current_user
from app.services.workflow.workflow_service import WorkflowService
from app.services.workflow.notification_service import NotificationService

router = APIRouter()


@router.get("/document/{document_id}", response_model=DocumentWorkflowResponse, summary="Consultar o inicializar flujo de trabajo de un documento")
def get_document_workflow(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna el estado de ciclo de vida, asignaciones y eventos de auditoría del documento."""
    service = WorkflowService(db)
    return service.get_or_create_workflow(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id
    )


@router.get("/{workflow_id}", response_model=DocumentWorkflowResponse, summary="Consultar detalle de expediente de flujo de trabajo")
def get_workflow_detail(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Consulta todas las entidades relacionadas del expediente (asignaciones, comentarios, correcciones, aprobaciones)."""
    service = WorkflowService(db)
    return service.get_workflow_detail(
        tenant_id=current_user.tenant_id,
        user=current_user,
        workflow_id=workflow_id
    )


@router.get("/{workflow_id}/allowed-transitions", response_model=List[AllowedTransitionOption], summary="Consultar transiciones disponibles con estado de guardas")
def get_allowed_transitions(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calcula las transiciones que el usuario actual puede ejecutar en este momento."""
    service = WorkflowService(db)
    wf = service.get_workflow_detail(
        tenant_id=current_user.tenant_id,
        user=current_user,
        workflow_id=workflow_id
    )
    return service.engine.get_allowed_transitions(wf, current_user)


@router.post("/{workflow_id}/assign", response_model=DocumentWorkflowResponse, summary="Asignar o reasignar equipo legal, fecha límite y gobernanza")
def assign_team(
    workflow_id: UUID,
    data: WorkflowAssignTeamRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Asigna abogado responsable, revisor jurídico, asistente, fecha fatal y prioridad."""
    service = WorkflowService(db)
    return service.assign_team(
        tenant_id=current_user.tenant_id,
        user=current_user,
        workflow_id=workflow_id,
        lawyer_id=data.assigned_lawyer_id,
        reviewer_id=data.reviewer_id,
        assistant_id=data.assistant_id,
        deadline_at=data.deadline_at,
        priority=data.priority,
        allow_assistant_approval=data.allow_assistant_approval
    )


@router.post("/{workflow_id}/transition", response_model=DocumentWorkflowResponse, summary="Ejecutar transición de estado configurable")
def execute_transition(
    workflow_id: UUID,
    data: WorkflowTransitionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aplica la transición de estado validando guardas de competencia y asentando auditoría."""
    service = WorkflowService(db)
    return service.execute_transition(
        tenant_id=current_user.tenant_id,
        user=current_user,
        workflow_id=workflow_id,
        target_state=data.target_state,
        reason=data.reason,
        metadata=data.metadata
    )


@router.post("/{workflow_id}/comments", response_model=WorkflowCommentResponse, status_code=status.HTTP_201_CREATED, summary="Agregar comentario interno al expediente")
def add_comment(
    workflow_id: UUID,
    data: CreateWorkflowCommentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Asienta una nota o comentario de trabajo visible para los integrantes del despacho."""
    service = WorkflowService(db)
    return service.add_comment(
        tenant_id=current_user.tenant_id,
        user=current_user,
        workflow_id=workflow_id,
        comment_text=data.comment_text,
        clause_reference=data.clause_reference,
        is_internal_only=data.is_internal_only
    )


@router.post("/{workflow_id}/corrections", response_model=CorrectionRequestResponse, status_code=status.HTTP_201_CREATED, summary="Solicitar formalmente una corrección jurídica")
def request_correction(
    workflow_id: UUID,
    data: CreateCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea una solicitud de corrección y pasa el expediente automáticamente al estado 'En corrección'."""
    service = WorkflowService(db)
    return service.request_correction(
        tenant_id=current_user.tenant_id,
        user=current_user,
        workflow_id=workflow_id,
        title=data.title,
        description=data.description,
        target_clause=data.target_clause,
        requested_to_id=data.requested_to_id
    )


@router.patch("/corrections/{correction_id}/resolve", response_model=CorrectionRequestResponse, summary="Resolver y solventar solicitud de corrección")
def resolve_correction(
    correction_id: UUID,
    data: ResolveCorrectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marca como solventada la corrección y reanuda el flujo a 'Pendiente de revisión'."""
    service = WorkflowService(db)
    return service.resolve_correction(
        tenant_id=current_user.tenant_id,
        user=current_user,
        correction_id=correction_id,
        resolution_notes=data.resolution_notes
    )


@router.post("/{workflow_id}/approve", response_model=WorkflowApprovalRecordResponse, status_code=status.HTTP_201_CREATED, summary="Aprobar documento formalmente (HITL)")
def submit_approval(
    workflow_id: UUID,
    data: SubmitApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Registra aprobación formal con alcance, versión y cédula profesional.
    Si es definitiva, traslada el expediente al estado 'Aprobado'.
    """
    service = WorkflowService(db)
    return service.submit_approval(
        tenant_id=current_user.tenant_id,
        user=current_user,
        workflow_id=workflow_id,
        scope=data.scope,
        reviewer_license=data.reviewer_license,
        notes=data.notes
    )


@router.get("/approvals/list", response_model=List[WorkflowApprovalRecordResponse], summary="Listar aprobaciones formales del despacho")
def list_tenant_approvals(
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna el historial de firmas y aprobaciones HITL del despacho."""
    if current_user.role == "SUPER_ADMIN":
        return []
    return (
        db.query(WorkflowApprovalRecord)
        .join(DocumentWorkflow, DocumentWorkflow.id == WorkflowApprovalRecord.workflow_id)
        .filter(DocumentWorkflow.tenant_id == current_user.tenant_id)
        .order_by(WorkflowApprovalRecord.approved_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


# Centro de Notificaciones In-App
@router.get("/notifications/list", response_model=List[WorkflowNotificationResponse], summary="Listar notificaciones del usuario actual")
def list_notifications(
    unread_only: bool = Query(False, description="Filtrar únicamente notificaciones no leídas"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Consulta el buzón de notificaciones jurídicas del usuario."""
    notif_service = NotificationService(db)
    return notif_service.list_user_notifications(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        unread_only=unread_only
    )


@router.get("/notifications/unread-count", summary="Obtener contador de notificaciones no leídas")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Contador optimizado para la campana de notificaciones de la barra superior."""
    notif_service = NotificationService(db)
    count = notif_service.get_unread_count(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )
    return {"unread_count": count}


@router.patch("/notifications/{notification_id}/read", response_model=WorkflowNotificationResponse, summary="Marcar notificación como leída")
def mark_notification_read(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza el estado de una notificación a leída."""
    notif_service = NotificationService(db)
    return notif_service.mark_as_read(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        notification_id=notification_id
    )


@router.post("/notifications/read-all", summary="Marcar todas las notificaciones como leídas")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marca como leídas todas las alertas del usuario."""
    notif_service = NotificationService(db)
    count = notif_service.mark_all_as_read(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id
    )
    return {"marked_read_count": count}
