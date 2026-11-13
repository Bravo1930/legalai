from datetime import datetime, timezone
from fastapi import APIRouter
import httpx
import redis
from app.core.config import settings
from app.core.logging import logger
from app.db.session import check_db_connection
from app.schemas.health import SystemHealthResponse, DatabaseHealth, RedisHealth, OllamaHealth

router = APIRouter()


@router.get("", response_model=SystemHealthResponse, summary="Verificación integral de salud de la plataforma")
async def health_check():
    """Ejecuta diagnósticos en tiempo real sobre PostgreSQL, Redis, Ollama y el runtime."""
    
    # 1. Diagnóstico de PostgreSQL
    db_info = check_db_connection()
    db_health = DatabaseHealth(
        status=db_info["status"],
        version=db_info.get("version"),
        pgvector_enabled=db_info.get("pgvector_enabled", False),
        error=db_info.get("error")
    )

    # 2. Diagnóstico de Redis
    redis_health = RedisHealth(status="unhealthy", connected=False)
    try:
        r = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD or None,
            socket_connect_timeout=0.2,
            socket_timeout=0.2
        )
        if r.ping():
            redis_health.status = "healthy"
            redis_health.connected = True
            redis_health.details = f"Conectado a {settings.REDIS_HOST}:{settings.REDIS_PORT}"
    except Exception as e:
        redis_health.details = f"Redis offline o en modo fallback: {str(e)}"

    # 3. Diagnóstico de Ollama Local
    ollama_health = OllamaHealth(
        status="unhealthy",
        base_url=settings.OLLAMA_BASE_URL,
        models_available=[]
    )
    headers = {"Content-Type": "application/json"}
    if settings.OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {settings.OLLAMA_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=1.0, verify=settings.OLLAMA_VERIFY_SSL) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                ollama_health.status = "healthy"
                ollama_health.models_available = models
            else:
                ollama_health.error = f"Respuesta HTTP {resp.status_code} desde Ollama"
    except Exception as e:
        ollama_health.error = f"No se pudo conectar a Ollama local: {str(e)}"

    # Estado global consolidado
    is_healthy = (db_health.status == "healthy")
    overall_status = "healthy" if (is_healthy and ollama_health.status == "healthy") else ("degraded" if is_healthy else "unhealthy")

    return SystemHealthResponse(
        status=overall_status,
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        timestamp=datetime.now(timezone.utc).isoformat(),
        database=db_health,
        redis=redis_health,
        ollama=ollama_health
    )
