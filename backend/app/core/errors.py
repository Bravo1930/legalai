from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError
from app.core.logging import logger


class AppException(Exception):
    """Excepción base para errores de negocio y aplicación."""
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_SERVER_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    def __init__(self, message: str = "Recurso no encontrado", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            details=details
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Credenciales inválidas o sesión expirada", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="UNAUTHORIZED",
            details=details
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "Acceso denegado. Permisos insuficientes.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            code="FORBIDDEN",
            details=details
        )


class ConflictException(AppException):
    def __init__(self, message: str = "Conflicto con el estado actual del recurso", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            details=details
        )


class ValidationException(AppException):
    def __init__(self, message: str = "Error de validación de datos", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            details=details
        )


class DatabaseException(AppException):
    def __init__(self, message: str = "Error en operación de base de datos", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="DATABASE_ERROR",
            details=details
        )


def build_error_response(status_code: int, code: str, message: str, details: Any, request: Request) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "NO_REQ_ID")
    try:
        safe_details = jsonable_encoder(details)
    except Exception:
        safe_details = str(details)
    content = {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": safe_details,
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
        }
    }
    return JSONResponse(status_code=status_code, content=content)


def setup_exception_handlers(app: FastAPI) -> None:
    """Registra manejadores de excepciones centralizados en la aplicación FastAPI."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(f"[{exc.code}] {exc.message} - Path: {request.url.path} - Details: {exc.details}")
        return build_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
            request=request
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(f"[VALIDATION_ERROR] Fallo de validación en: {request.url.path}")
        safe_errors = []
        for err in exc.errors():
            loc = err.get("loc", ())
            msg = err.get("msg", "")
            err_type = err.get("type", "")
            safe_errors.append({
                "loc": [str(x) for x in loc],
                "msg": str(msg),
                "type": str(err_type)
            })
        return build_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="REQUEST_VALIDATION_ERROR",
            message="Los parámetros enviados no cumplen con el esquema requerido",
            details=safe_errors,
            request=request
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.error(f"[DATABASE_ERROR] Error crítico en SQLAlchemy: {str(exc)}", exc_info=True)
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="DATABASE_ERROR",
            message="Ocurrió un error al persistir o consultar la base de datos",
            details=str(exc) if getattr(request.app.state, "debug", False) else {},
            request=request
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.critical(f"[UNHANDLED_EXCEPTION] Excepción no controlada: {str(exc)}", exc_info=True)
        return build_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="UNHANDLED_SERVER_ERROR",
            message="Ocurrió un error inesperado en el servidor",
            details=str(exc) if getattr(request.app.state, "debug", False) else {},
            request=request
        )
