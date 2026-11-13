from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class TaskCreate(BaseModel):
    task_type: str = Field(..., description="Tipo de tarea asíncrona: OCR_EXTRACTION, EMBEDDING_INGESTION, etc.")
    payload: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    task_type: str
    status: str
    payload: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
