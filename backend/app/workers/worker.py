import time
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import redis
from app.core.config import settings
from app.core.logging import logger
from app.db.session import SessionLocal
from app.db.base import Base, Tenant, User, AuditLog, Task
from app.models.task import TaskStatus
from app.services.task_service import TaskService


def process_task_logic(task_type: str, payload: dict) -> dict:
    """Ejecuta la lógica especializada de la tarea."""
    logger.info(f"Procesando trabajo: {task_type} con payload: {payload}")
    time.sleep(1.5)  # Simulación de cómputo de OCR / vectorización
    
    if task_type == "OCR_EXTRACTION":
        return {
            "status": "success",
            "pages_processed": payload.get("pages", 1),
            "text_length": 1540,
            "confidence_score": 0.985,
            "detected_jurisdiction": "FEDERAL_MEXICO"
        }
    elif task_type == "EMBEDDING_INGESTION":
        return {
            "status": "success",
            "model_used": settings.OLLAMA_EMBEDDING_MODEL,
            "chunks_embedded": payload.get("chunks", 5),
            "dimensions": 1024
        }
    elif task_type == "CONTRACT_ANALYSIS":
        return {
            "status": "success",
            "model_used": settings.OLLAMA_LLM_MODEL,
            "clauses_reviewed": 18,
            "risk_flags": [
                {"clause": "Pena convencional", "level": "MEDIUM", "recommendation": "Revisar apego al Código Civil Federal"}
            ]
        }
    else:
        return {
            "status": "success",
            "message": f"Tarea {task_type} procesada correctamente",
            "processed_at": datetime.now(timezone.utc).isoformat()
        }


def run_worker_loop():
    """Bucle principal del trabajador asíncrono con soporte de Redis y PostgreSQL."""
    logger.info("Iniciando LegalAI Task Worker...")
    
    # Intentar conexión con Redis
    r = None
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            socket_connect_timeout=2
        )
        r.ping()
        logger.info(f"Worker conectado exitosamente al broker Redis ({settings.REDIS_HOST}:{settings.REDIS_PORT}).")
    except Exception as e:
        logger.warning(f"Worker no pudo conectar a Redis ({e}). Operando en modo sondeo PostgreSQL.")
        r = None

    while True:
        db: Session = SessionLocal()
        try:
            task_to_process = None

            # 1. Intentar obtener tarea de Redis
            if r:
                try:
                    queue_item = r.brpop("legal_ai_tasks_queue", timeout=3)
                    if queue_item:
                        _, message_raw = queue_item
                        data = json.loads(message_raw.decode("utf-8"))
                        task_id = uuid.UUID(data["task_id"])
                        task_to_process = db.query(Task).filter(Task.id == task_id).first()
                except Exception as e:
                    logger.debug(f"Error al leer de Redis: {e}")

            # 2. Si no hubo tarea de Redis, buscar pendientes en BD
            if not task_to_process:
                task_to_process = db.query(Task).filter(
                    Task.status == TaskStatus.PENDING
                ).order_by(Task.created_at.asc()).first()

            # 3. Procesar si hay tarea disponible
            if task_to_process:
                logger.info(f"Iniciando ejecución de tarea {task_to_process.id} ({task_to_process.task_type})")
                TaskService.update_task_status(db, task_to_process.id, TaskStatus.PROCESSING)
                
                try:
                    result = process_task_logic(task_to_process.task_type, task_to_process.payload or {})
                    TaskService.update_task_status(db, task_to_process.id, TaskStatus.COMPLETED, result=result)
                    logger.info(f"Tarea {task_to_process.id} completada exitosamente.")
                except Exception as ex:
                    logger.error(f"Error procesando tarea {task_to_process.id}: {ex}")
                    TaskService.update_task_status(db, task_to_process.id, TaskStatus.FAILED, error_message=str(ex))
            else:
                time.sleep(2)

        except Exception as loop_ex:
            logger.error(f"Error en bucle del worker: {loop_ex}")
            time.sleep(3)
        finally:
            db.close()


if __name__ == "__main__":
    run_worker_loop()
