from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.advanced_analysis import (
    AdvancedAnalysisSessionResponse,
    LegalFindingResponse,
    FindingReviewRequest,
    VersionComparisonRequest,
    VersionComparisonResponse
)
from app.services.auth_service import get_current_user
from app.services.analysis.advanced_analysis_engine import AdvancedAnalysisEngine

router = APIRouter()


@router.post("/analyze/{document_id}", response_model=AdvancedAnalysisSessionResponse, status_code=status.HTTP_201_CREATED, summary="Ejecutar análisis jurídico documental integral")
def run_advanced_analysis(
    document_id: UUID,
    version_id: Optional[UUID] = Query(None, description="ID de versión específica a analizar"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ejecuta el motor avanzado de análisis jurídico documental:
    - Descomposición y resumen cláusula por cláusula.
    - Detección de obligaciones, derechos, plazos y penalizaciones.
    - Identificación de contradicciones internas y omisiones esenciales.
    - Auditoría contra políticas internas y catálogo de leyes mexicanas.
    - Asignación de severidades y cálculo del índice de riesgo (herramienta de priorización).
    """
    engine = AdvancedAnalysisEngine(db)
    return engine.analyze_document(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id,
        version_id=version_id
    )


@router.get("/document/{document_id}", response_model=Optional[AdvancedAnalysisSessionResponse], summary="Consultar última sesión de análisis avanzado")
def get_latest_document_analysis(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna la sesión de análisis más reciente para el documento seleccionado."""
    engine = AdvancedAnalysisEngine(db)
    return engine.get_latest_session(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id
    )


@router.post("/findings/{finding_id}/review", response_model=LegalFindingResponse, summary="Validación o descarte humano (HITL) de un hallazgo")
def review_finding(
    finding_id: UUID,
    review_data: FindingReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permite que un abogado con cédula profesional valide, modifique o descarte una observación
    generada por el análisis jurídico (principio Human-in-the-Loop).
    """
    engine = AdvancedAnalysisEngine(db)
    return engine.review_finding(
        tenant_id=current_user.tenant_id,
        lawyer_user=current_user,
        finding_id=finding_id,
        status_val=review_data.review_status,
        reviewer_license=review_data.reviewer_license,
        reviewer_notes=review_data.reviewer_notes
    )


@router.post("/compare/{document_id}", response_model=VersionComparisonResponse, status_code=status.HTTP_201_CREATED, summary="Comparación analítica entre versiones (Redline & Risk Delta)")
def compare_versions(
    document_id: UUID,
    data: VersionComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compara dos versiones del documento:
    - Identifica cláusulas añadidas, suprimidas o modificadas.
    - Calcula el delta de riesgos (mitigados, introducidos, persistentes).
    - Emite resumen ejecutivo comparativo.
    """
    engine = AdvancedAnalysisEngine(db)
    return engine.compare_document_versions(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id,
        base_text=data.base_text,
        compare_text=data.compare_text,
        base_label=data.base_label,
        compare_label=data.compare_label
    )
