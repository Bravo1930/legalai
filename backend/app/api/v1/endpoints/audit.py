from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from app.db.session import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.auth_service import get_current_user
from app.core.errors import ForbiddenException

router = APIRouter()


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID] = None
    user_name: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime


@router.get("", response_model=List[AuditLogResponse], summary="Consultar registro inmutable de auditoría forense")
def list_audit_logs(
    action: Optional[str] = Query(None, description="Filtrar por tipo de acción"),
    resource_type: Optional[str] = Query(None, description="Filtrar por tipo de recurso"),
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retorna la bitácora de auditoría inmutable del despacho para trazabilidad de operaciones,
    accesos y modificaciones legales.
    """
    if current_user.role == "SUPER_ADMIN":
        q = db.query(AuditLog)
    else:
        q = db.query(AuditLog).filter(AuditLog.tenant_id == current_user.tenant_id)

    if action:
        q = q.filter(AuditLog.action == action)
    if resource_type:
        q = q.filter(AuditLog.resource_type == resource_type)

    logs = q.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()

    # Mapear nombres de usuario para la respuesta
    res = []
    for log in logs:
        u_name = log.user.full_name if log.user else "Sistema"
        res.append(
            AuditLogResponse(
                id=log.id,
                tenant_id=log.tenant_id,
                user_id=log.user_id,
                user_name=u_name,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                created_at=log.created_at
            )
        )

    return res
