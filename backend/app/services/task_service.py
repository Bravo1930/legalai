import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
import redis
from app.core.config import settings
from app.core.logging import logger
from app.core.errors import NotFoundException
from app.models.task import Task, TaskStatus


class TaskService:
    @staticmethod
    def _get_redis_client() -> Optional[redis.Redis]:
        try:
            r = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD or None,
                socket_connect_timeout=0.3,
                socket_timeout=0.3
            )
            r.ping()
            return r
        except Exception as e:
            logger.debug(f"Redis no disponible directamente ({e}). Operando con cola transaccional en PostgreSQL.")
            return None

    @staticmethod
    def enqueue_task(
        db: Session,
        tenant_id: UUID,
        task_type: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Crea y registra una tarea asíncrona, encolándola en Redis o en la base de datos."""
        task = Task(
            tenant_id=tenant_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            payload=payload or {}
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # Si Redis está disponible, encolamos el ID para el worker distribuido
        r = TaskService._get_redis_client()
        if r:
            try:
                task_msg = json.dumps({"task_id": str(task.id), "tenant_id": str(tenant_id), "type": task_type})
                r.lpush("legal_ai_tasks_queue", task_msg)
                logger.info(f"Tarea {task.id} ({task_type}) encolada en Redis.")
            except Exception as e:
                logger.warning(f"No se pudo enviar a Redis, quedará encolada en PostgreSQL: {e}")

        return task

    @staticmethod
    def get_task(db: Session, task_id: UUID, tenant_id: UUID) -> Task:
        task = db.query(Task).filter(Task.id == task_id, Task.tenant_id == tenant_id).first()
        if not task:
            raise NotFoundException("Tarea asíncrona no encontrada")
        return task

    @staticmethod
    def list_tasks_by_tenant(db: Session, tenant_id: UUID, skip: int = 0, limit: int = 50) -> List[Task]:
        return db.query(Task).filter(Task.tenant_id == tenant_id).order_by(Task.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def update_task_status(
        db: Session,
        task_id: UUID,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ) -> Task:
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise NotFoundException("Tarea no encontrada")

        task.status = status
        if result is not None:
            task.result = result
        if error_message is not None:
            task.error_message = error_message
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def process_pending_tasks_batch(db: Session, max_tasks: int = 5) -> int:
        """
        Procesa tareas pendientes encoladas o reintenta tareas atoradas en PROCESSING.
        Actualiza el estado a COMPLETED con resultados estructurados, o a FAILED con mensaje de error.
        """
        from datetime import timedelta
        from app.workers.worker import process_task_logic

        now = datetime.now(timezone.utc)

        # 1. Recuperar tareas atoradas en PROCESSING por más de 5 minutos y devolverlas a PENDING
        stuck_threshold = now - timedelta(minutes=5)
        stuck_tasks = db.query(Task).filter(
            Task.status == TaskStatus.PROCESSING,
            Task.updated_at < stuck_threshold
        ).all()
        for st in stuck_tasks:
            logger.warning(f"Reintentando tarea asíncrona previamente atorada {st.id} ({st.task_type})")
            st.status = TaskStatus.PENDING
            st.updated_at = now
            db.commit()

        # 2. Obtener lote de tareas PENDING
        pending_tasks = db.query(Task).filter(
            Task.status == TaskStatus.PENDING
        ).order_by(Task.created_at.asc()).limit(max_tasks).all()

        processed_count = 0
        for task in pending_tasks:
            task.status = TaskStatus.PROCESSING
            task.updated_at = datetime.now(timezone.utc)
            db.commit()

            try:
                logger.info(f"Worker procesando tarea {task.id} [{task.task_type}]...")
                result = process_task_logic(task.task_type, task.payload or {})
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.error_message = None
                task.completed_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                db.commit()
                processed_count += 1
                logger.info(f"Tarea {task.id} completada exitosamente.")
            except Exception as ex:
                logger.error(f"Error al ejecutar tarea asíncrona {task.id}: {ex}")
                task.status = TaskStatus.FAILED
                task.error_message = f"Error de procesamiento: {str(ex)}"
                task.completed_at = datetime.now(timezone.utc)
                task.updated_at = datetime.now(timezone.utc)
                db.commit()
                processed_count += 1

        return processed_count
