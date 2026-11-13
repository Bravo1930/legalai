from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.ai import AIAnalysis
from app.schemas.ai import AIModelInfo, AIAnalysisRequest, AIAnalysisResponse
from app.services.ai.ollama_client import ollama_client
from app.services.ai.orchestrator import AIOrchestrator
from app.services.auth_service import get_current_user
from app.core.errors import ForbiddenException, NotFoundException

router = APIRouter()


@router.get("/models", response_model=List[AIModelInfo], summary="Listar modelos locales instalados en Ollama")
async def list_ai_models(current_user: User = Depends(get_current_user)):
    """Consulta los modelos reales disponibles en la instancia local de Ollama (localhost:11434)."""
    raw_models = await ollama_client.list_models()
    models_info = []
    for m in raw_models:
        details = m.get("details", {})
        models_info.append(AIModelInfo(
            name=m["name"],
            size_bytes=m.get("size", 0),
            parameter_size=details.get("parameter_size"),
            quantization_level=details.get("quantization_level"),
            capabilities=m.get("capabilities", []),
            family=details.get("family")
        ))
    return models_info


@router.post("/analyze/{document_id}", response_model=AIAnalysisResponse, summary="Ejecutar análisis de IA con agente especializado")
async def analyze_document(
    document_id: UUID,
    request: AIAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ejecuta un agente de IA (Clasificador, Extractor, Analista, Riesgos, Redactor, Verificador)
    utilizando Ollama local con aislamiento estricto y cero filtración externa.
    """
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("El administrador de plataforma no tiene acceso al análisis de documentos de despachos.")

    return await AIOrchestrator.analyze_document(
        db=db,
        tenant_id=current_user.tenant_id,
        document_id=document_id,
        agent_type=request.agent_type,
        model=request.model,
        user_prompt=request.user_prompt,
        user_id=current_user.id
    )


@router.get("/analyses/{document_id}", response_model=List[AIAnalysisResponse], summary="Historial de análisis de un documento")
def list_document_analyses(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consulta todas las evaluaciones y dictámenes generados por los agentes de IA para este documento."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("Acceso restringido al plano de control.")

    return AIOrchestrator.list_analyses_for_document(
        db=db,
        tenant_id=current_user.tenant_id,
        document_id=document_id
    )


@router.get("/analyses/detail/{analysis_id}", response_model=AIAnalysisResponse, summary="Detalle de un análisis específico")
def get_analysis_detail(
    analysis_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtiene la salida estructurada completa, prompts y métricas de consumo de una corrida de IA."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("Acceso restringido al plano de control.")

    analysis = db.query(AIAnalysis).filter(
        AIAnalysis.id == analysis_id,
        AIAnalysis.tenant_id == current_user.tenant_id
    ).first()

    if not analysis:
        raise NotFoundException("Análisis no encontrado en este despacho")

    return analysis
