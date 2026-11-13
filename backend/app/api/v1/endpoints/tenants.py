from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.security import LegalRoles
from app.schemas.tenant import TenantCreate, TenantResponse
from app.schemas.common import APIResponse
from app.models.user import User
from app.services.tenant_service import TenantService
from app.services.auth_service import get_current_user, require_roles

router = APIRouter()


@router.post("", response_model=TenantResponse, summary="Registrar nuevo despacho jurídico (SaaS)")
def create_tenant(
    tenant_in: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([LegalRoles.SUPER_ADMIN]))
):
    """Crea una nueva organización o bufete jurídico."""
    return TenantService.create_tenant(db=db, tenant_in=tenant_in, creator_id=current_user.id)


@router.get("", response_model=List[TenantResponse], summary="Listar despachos registrados")
def list_tenants(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([LegalRoles.SUPER_ADMIN]))
):
    """Lista despachos (restringido a superadministradores de la plataforma)."""
    return TenantService.list_tenants(db=db, skip=skip, limit=limit)


@router.get("/{tenant_id}", response_model=TenantResponse, summary="Obtener detalles de un despacho")
def get_tenant(
    tenant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consulta la información de un despacho (aislado a su propio despacho a menos que sea SUPER_ADMIN)."""
    if current_user.role != LegalRoles.SUPER_ADMIN and current_user.tenant_id != tenant_id:
        from app.core.errors import ForbiddenException
        raise ForbiddenException("No tiene autorización para consultar datos de otro despacho")
        
    return TenantService.get_tenant_by_id(db=db, tenant_id=tenant_id)
