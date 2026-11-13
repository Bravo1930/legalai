import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configura el sistema centralizado de logging para la plataforma."""
    logger = logging.getLogger("legal_ai")
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Evitar duplicar handlers en reinicios
    if logger.handlers:
        return logger

    # Formato unificado para auditoría y trazabilidad
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s] [ReqID: %(request_id)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler para consola (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Filtro para inyectar request_id por defecto si no existe en el contexto
    class RequestIDFilter(logging.Filter):
        def filter(self, record):
            if not hasattr(record, "request_id"):
                record.request_id = "SYS"
            return True

    console_handler.addFilter(RequestIDFilter())
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para archivo de log si está configurado
    if settings.LOG_FILE_PATH:
        try:
            log_dir = os.path.dirname(settings.LOG_FILE_PATH)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            file_handler = RotatingFileHandler(
                settings.LOG_FILE_PATH,
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
                encoding="utf-8"
            )
            file_handler.setLevel(log_level)
            file_handler.addFilter(RequestIDFilter())
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"No se pudo inicializar RotatingFileHandler: {e}")

    return logger


logger = setup_logging()
