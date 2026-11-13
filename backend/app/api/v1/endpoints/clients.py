from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientResponse
from app.core.errors import NotFoundException, ForbiddenException
from app.services.auth_service import get_current_user

router = APIRouter()


@router.post("", response_model=ClientResponse, summary="Registrar nuevo cliente del despacho")
def create_client(
    client_in: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registra un cliente (persona física o moral) aislado al despacho del usuario."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("El administrador de plataforma no puede gestionar clientes de despachos.")

    client = Client(
        tenant_id=current_user.tenant_id,
        name=client_in.name.strip(),
        rfc=client_in.rfc.strip().upper() if client_in.rfc else None,
        curp=client_in.curp.strip().upper() if client_in.curp else None,
        client_type=client_in.client_type,
        contact_email=client_in.contact_email,
        contact_phone=client_in.contact_phone,
        address=client_in.address
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=List[ClientResponse], summary="Listar clientes del despacho")
def list_clients(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna los clientes pertenecientes al despacho del solicitante."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("El administrador de plataforma no puede consultar clientes de despachos.")

    return db.query(Client).filter(
        Client.tenant_id == current_user.tenant_id
    ).order_by(Client.name.asc()).offset(skip).limit(limit).all()


@router.get("/{client_id}", response_model=ClientResponse, summary="Obtener detalles de un cliente")
def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Consulta la ficha de un cliente con protección horizontal IDOR."""
    if current_user.role == "SUPER_ADMIN":
        raise ForbiddenException("Acceso restringido al plano de control.")

    client = db.query(Client).filter(
        Client.id == client_id,
        Client.tenant_id == current_user.tenant_id
    ).first()

    if not client:
        raise NotFoundException("Cliente no encontrado en este despacho")

    return client
