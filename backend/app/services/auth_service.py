from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import verify_password, get_password_hash, create_access_token, decode_access_token
from app.core.errors import UnauthorizedException, ForbiddenException, NotFoundException
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import LoginRequest, TokenResponse, UserProfileSummary

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


class AuthService:
    @staticmethod
    def authenticate_user(
        db: Session,
        login_data: LoginRequest,
        client_ip: Optional[str] = None
    ) -> TokenResponse:
        # Búsqueda por email
        user_query = db.query(User).join(Tenant).filter(User.email == login_data.email)
        
        if login_data.tenant_slug:
            user_query = user_query.filter(Tenant.slug == login_data.tenant_slug)
        
        user = user_query.first()
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise UnauthorizedException("Credenciales inválidas o correo no registrado")

        if not user.is_active:
            raise ForbiddenException("La cuenta de usuario se encuentra inactiva")

        if not user.tenant.is_active:
            raise ForbiddenException("El despacho asignado se encuentra suspendido")

        # Registro en AuditLog (Trazabilidad forense inmutable)
        audit = AuditLog(
            tenant_id=user.tenant_id,
            user_id=user.id,
            action="USER_LOGIN",
            resource_type="USER",
            resource_id=str(user.id),
            details={"email": user.email, "role": user.role},
            ip_address=client_ip
        )
        db.add(audit)
        db.commit()

        # Generación de token JWT
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
            "tenant_slug": user.tenant.slug,
            "role": user.role,
            "professional_license": user.professional_license or ""
        }
        token = create_access_token(data=token_payload)

        user_summary = UserProfileSummary(
            id=user.id,
            tenant_id=user.tenant_id,
            tenant_name=user.tenant.name,
            tenant_slug=user.tenant.slug,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            professional_license=user.professional_license,
            is_active=user.is_active
        )

        return TokenResponse(
            access_token=token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            user=user_summary
        )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Extrae y valida el usuario activo a partir del token JWT."""
    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Token inválido o expirado")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token sin identificador de usuario válido")

    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise UnauthorizedException("Identificador de usuario corrupto en token")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user or not user.is_active:
        raise UnauthorizedException("Usuario inexistente o inactivo")

    return user


def require_roles(allowed_roles: list):
    """Filtro de autorización RBAC basado en roles del usuario."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise ForbiddenException(f"Acceso denegado. Se requiere uno de los siguientes roles: {', '.join(allowed_roles)}")
        return current_user
    return role_checker
