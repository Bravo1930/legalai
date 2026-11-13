from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AIModelInfo(BaseModel):
    name: str
    size_bytes: int
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None
    capabilities: List[str] = []
    family: Optional[str] = None


class AIAnalysisRequest(BaseModel):
    agent_type: str = Field(
        "CLASSIFIER",
        description="Agente a ejecutar: CLASSIFIER, EXTRACTOR, CLAUSE_ANALYST, RISK_DETECTOR, RESEARCHER, DRAFTER, VERIFIER, FULL_SUITE"
    )
    model: Optional[str] = Field(None, description="Modelo Ollama a utilizar (opcional, si es null selecciona el óptimo)")
    user_prompt: Optional[str] = Field(None, description="Instrucción específica adicional para el agente")


class AIAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    document_id: UUID
    agent_type: str
    model_used: str
    structured_output: Dict[str, Any]
    tokens_prompt: int
    tokens_completion: int
    latency_ms: int
    created_at: datetime
