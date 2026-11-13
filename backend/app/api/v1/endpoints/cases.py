from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.case import Case
from app.models.client import Client
from app.schemas.case import CaseCreate, CaseResponse
from app.core.errors import NotFoundException, ForbiddenException
from app.services.auth_service import get_current_user

router = APIRouter()


@router.post("", response_model=CaseResponse, summary="Aperturar nuevo expediente o asunto jurídico")
def create_case(
    case_in: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea un expediente judicial o corporativo dentro del despacho."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("El administrador de plataforma no puede gestionar expedientes de despachos.")

    # Validar que el cliente pertenezca al despacho
    client = db.query(Client).filter(
        Client.id == case_in.client_id,
        Client.tenant_id == current_user.tenant_id
    ).first()
    if not client:
        raise NotFoundException("El cliente indicado no pertenece a este despacho")

    case = Case(
        tenant_id=current_user.tenant_id,
        client_id=case_in.client_id,
        lead_lawyer_id=current_user.id,
        case_number=case_in.case_number.strip(),
        title=case_in.title.strip(),
        description=case_in.description,
        matter=case_in.matter,
        jurisdiction=case_in.jurisdiction,
        state=case_in.state,
        court_authority=case_in.court_authority
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.get("", response_model=List[CaseResponse], summary="Listar expedientes del despacho")
def list_cases(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna los expedientes del despacho del usuario."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("Acceso restringido al plano de control.")

    return db.query(Case).filter(
        Case.tenant_id == current_user.tenant_id
    ).order_by(Case.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{case_id}", response_model=CaseResponse, summary="Obtener detalles de un expediente")
def get_case(
    case_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consulta la ficha de un expediente con protección horizontal."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("Acceso restringido al plano de control.")

    case = db.query(Case).filter(
        Case.id == case_id,
        Case.tenant_id == current_user.tenant_id
    ).first()

    if not case:
        raise NotFoundException("Expediente no encontrado en este despacho")

    return case
