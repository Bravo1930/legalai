from typing import List, Optional
from pydantic import BaseModel


class ServiceComponentStatus(BaseModel):
    status: str  # healthy | degraded | unhealthy
    details: Optional[str] = None


class DatabaseHealth(BaseModel):
    status: str
    version: Optional[str] = None
    pgvector_enabled: bool = False
    error: Optional[str] = None


class RedisHealth(BaseModel):
    status: str
    connected: bool = False
    details: Optional[str] = None


class OllamaHealth(BaseModel):
    status: str
    base_url: str
    models_available: List[str] = []
    error: Optional[str] = None


class SystemHealthResponse(BaseModel):
    status: str  # healthy | degraded | unhealthy
    environment: str
    version: str
    timestamp: str
    database: DatabaseHealth
    redis: RedisHealth
    ollama: OllamaHealth
