from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.task import TaskCreate, TaskResponse
from app.models.user import User
from app.services.task_service import TaskService
from app.services.auth_service import get_current_user

router = APIRouter()


@router.post("", response_model=TaskResponse, summary="Encolar nueva tarea asíncrona")
def enqueue_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Encola un trabajo (OCR, chunking, embeddings, análisis) para ser ejecutado asíncronamente."""
    return TaskService.enqueue_task(
        db=db,
        tenant_id=current_user.tenant_id,
        task_type=task_in.task_type,
        payload=task_in.payload
    )


@router.get("/{task_id}", response_model=TaskResponse, summary="Consultar estado de una tarea")
def get_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el progreso, estado o resultado de una tarea encolada."""
    return TaskService.get_task(
        db=db,
        task_id=task_id,
        tenant_id=current_user.tenant_id
    )


@router.get("", response_model=List[TaskResponse], summary="Listar tareas del despacho")
def list_tasks(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista las tareas encoladas y completadas para el despacho del usuario."""
    return TaskService.list_tasks_by_tenant(
        db=db,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )


@router.post("/{task_id}/retry", response_model=TaskResponse, summary="Reintentar tarea fallida o atorada")
def retry_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reintenta una tarea asíncrona devolviéndola al estado PENDING para ser procesada por el worker."""
    task = TaskService.get_task(db=db, task_id=task_id, tenant_id=current_user.tenant_id)
    task.status = "PENDING"
    task.error_message = None
    task.completed_at = None
    db.commit()
    db.refresh(task)
    return task
