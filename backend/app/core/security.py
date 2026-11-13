from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import settings

# Contexto de hashing seguro para credenciales
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LegalRoles:
    SUPER_ADMIN = "SUPER_ADMIN"
    MANAGING_PARTNER = "MANAGING_PARTNER"  # Socio Director del Despacho
    SENIOR_LAWYER = "SENIOR_LAWYER"        # Abogado Senior (Facultad de Aprobación HITL)
    ASSOCIATE_LAWYER = "ASSOCIATE_LAWYER"  # Abogado Asociado
    PARALEGAL = "PARALEGAL"                # Pasante / Asistente Jurídico
    AUDITOR = "AUDITOR"                    # Auditor de Cumplimiento (Solo Lectura)

    ALL_ROLES = [
        SUPER_ADMIN,
        MANAGING_PARTNER,
        SENIOR_LAWYER,
        ASSOCIATE_LAWYER,
        PARALEGAL,
        AUDITOR,
    ]

    HITL_APPROVER_ROLES = [
        SUPER_ADMIN,
        MANAGING_PARTNER,
        SENIOR_LAWYER,
    ]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash almacenado."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Genera un hash seguro para la contraseña."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Genera un token de acceso JWT firmado con claims de tenant y rol."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": now,
        "iss": "legal-ai-mexico-auth"
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica y valida la firma y expiración de un token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
