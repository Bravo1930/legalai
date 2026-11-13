from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.rule import (
    LegalRuleCreate, LegalRuleUpdate, LegalRuleResponse, RuleStatusToggle,
    RuleEvaluationResponse, RuleEvaluationDetailResponse, RuleVerificationRequest
)
from app.services.auth_service import get_current_user
from app.services.rules.rule_service import RuleService

router = APIRouter()


@router.get("", response_model=List[LegalRuleResponse], summary="Listar catálogo de reglas deterministas del despacho")
def list_rules(
    category: Optional[str] = Query(None, description="Filtrar por categoría (RuleCategory)"),
    severity: Optional[str] = Query(None, description="Filtrar por severidad"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna las reglas deterministas configuradas para la organización del usuario."""
    service = RuleService(db)
    return service.list_rules(
        tenant_id=current_user.tenant_id,
        category=category,
        severity=severity,
        is_active=is_active,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=LegalRuleResponse, status_code=status.HTTP_201_CREATED, summary="Crear una nueva regla determinista")
def create_rule(
    data: LegalRuleCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea una regla determinista con versionado v1 automático y pista de auditoría."""
    service = RuleService(db)
    return service.create_rule(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        data=data
    )


@router.get("/{rule_id}", response_model=LegalRuleResponse, summary="Consultar detalle de regla y su historial de versiones")
def get_rule(
    rule_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna el detalle completo de una regla incluyendo su historial de versiones inmutables."""
    service = RuleService(db)
    return service.get_rule(tenant_id=current_user.tenant_id, rule_id=rule_id)


@router.put("/{rule_id}", response_model=LegalRuleResponse, summary="Modificar regla determinista (genera nueva versión)")
def update_rule(
    rule_id: UUID,
    data: LegalRuleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualiza una regla, incrementa su número de versión e inscribe la justificación en auditoría."""
    service = RuleService(db)
    return service.update_rule(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        rule_id=rule_id,
        data=data
    )


@router.patch("/{rule_id}/status", response_model=LegalRuleResponse, summary="Activar o desactivar regla determinista")
def toggle_rule_status(
    rule_id: UUID,
    data: RuleStatusToggle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Habilita o deshabilita la evaluación de una regla sin eliminar su historial."""
    service = RuleService(db)
    return service.set_rule_status(
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        rule_id=rule_id,
        is_active=data.is_active,
        reason=data.reason
    )


@router.post("/evaluate/{document_id}", response_model=RuleEvaluationResponse, status_code=status.HTTP_201_CREATED, summary="Ejecutar evaluación determinista sobre un documento")
def evaluate_document(
    document_id: UUID,
    rule_ids: Optional[List[UUID]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ejecuta el motor determinista de reglas contra el texto y metadatos del documento.
    Calcula evidencias textuales y genera dictamen reproducible al 100%.
    """
    service = RuleService(db)
    return service.evaluate_document_rules(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id,
        rule_ids=rule_ids
    )


@router.get("/evaluations/{document_id}", response_model=List[RuleEvaluationResponse], summary="Historial de evaluaciones de un documento")
def list_document_evaluations(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retorna las evaluaciones deterministas ejecutadas previamente sobre este documento."""
    service = RuleService(db)
    return service.list_document_evaluations(
        tenant_id=current_user.tenant_id,
        user=current_user,
        document_id=document_id
    )


@router.get("/evaluations/detail/{evaluation_id}", response_model=RuleEvaluationResponse, summary="Consultar detalle de una evaluación con evidencias")
def get_evaluation_detail(
    evaluation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Consulta el detalle de una evaluación determinista línea por línea."""
    service = RuleService(db)
    return service.get_evaluation(
        tenant_id=current_user.tenant_id,
        user=current_user,
        evaluation_id=evaluation_id
    )


@router.post("/evaluations/detail/{detail_id}/verify", response_model=RuleEvaluationDetailResponse, summary="Validación humana (HITL) de un hallazgo pendiente")
def verify_evaluation_detail(
    detail_id: UUID,
    verification: RuleVerificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Permite que un abogado humano resuelva un criterio clasificado como PENDING_HUMAN_REVIEW,
    recalculando el índice de cumplimiento determinista del documento.
    """
    service = RuleService(db)
    return service.verify_evaluation_detail(
        tenant_id=current_user.tenant_id,
        lawyer_user=current_user,
        detail_id=detail_id,
        verification=verification
    )
