from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserProfileSummary
from app.models.user import User
from app.services.auth_service import AuthService, get_current_user

router = APIRouter()


@router.post("/login", response_model=TokenResponse, summary="Autenticación de usuario y emisión de JWT")
def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """Inicia sesión y genera token con claims de despacho y perfil."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if client_ip in ("testclient", "localhost", None):
        client_ip = "127.0.0.1"
    return AuthService.authenticate_user(db=db, login_data=login_data, client_ip=client_ip)


@router.get("/me", response_model=UserProfileSummary, summary="Obtener perfil del usuario autenticado")
def get_me(current_user: User = Depends(get_current_user)):
    """Retorna información del usuario en sesión, su rol y despacho asignado."""
    return UserProfileSummary(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        tenant_name=current_user.tenant.name,
        tenant_slug=current_user.tenant.slug,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        professional_license=current_user.professional_license,
        is_active=current_user.is_active
    )
