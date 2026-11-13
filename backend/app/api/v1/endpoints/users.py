from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import LegalRoles
from app.schemas.user import UserCreate, UserResponse
from app.models.user import User
from app.services.tenant_service import TenantService
from app.services.auth_service import get_current_user, require_roles

router = APIRouter()


@router.post("", response_model=UserResponse, summary="Crear usuario en el despacho actual")
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([LegalRoles.SUPER_ADMIN, LegalRoles.MANAGING_PARTNER]))
):
    """Crea un nuevo abogado o integrante dentro del despacho del solicitante."""
    return TenantService.create_user_for_tenant(
        db=db,
        tenant_id=current_user.tenant_id,
        user_in=user_in,
        creator_id=current_user.id
    )


@router.get("", response_model=List[UserResponse], summary="Listar usuarios del despacho")
def list_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna los integrantes pertenecientes exclusivamente al despacho del usuario autenticado."""
    return TenantService.list_users_by_tenant(
        db=db,
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit
    )
