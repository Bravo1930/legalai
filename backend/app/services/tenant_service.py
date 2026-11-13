from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.core.errors import ConflictException, NotFoundException
from app.models.tenant import Tenant
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.schemas.user import UserCreate


class TenantService:
    @staticmethod
    def create_tenant(db: Session, tenant_in: TenantCreate, creator_id: Optional[UUID] = None) -> Tenant:
        existing = db.query(Tenant).filter(Tenant.slug == tenant_in.slug).first()
        if existing:
            raise ConflictException(f"Ya existe un despacho registrado con el identificador '{tenant_in.slug}'")

        tenant = Tenant(
            name=tenant_in.name,
            slug=tenant_in.slug.lower().strip(),
            rfc=tenant_in.rfc.upper().strip() if tenant_in.rfc else None,
            contact_email=tenant_in.contact_email.lower().strip()
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

        # Audit
        audit = AuditLog(
            tenant_id=tenant.id,
            user_id=creator_id,
            action="CREATE_TENANT",
            resource_type="TENANT",
            resource_id=str(tenant.id),
            details={"name": tenant.name, "slug": tenant.slug}
        )
        db.add(audit)
        db.commit()

        return tenant

    @staticmethod
    def get_tenant_by_id(db: Session, tenant_id: UUID) -> Tenant:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            raise NotFoundException("Despacho jurídico no encontrado")
        return tenant

    @staticmethod
    def list_tenants(db: Session, skip: int = 0, limit: int = 50) -> List[Tenant]:
        return db.query(Tenant).offset(skip).limit(limit).all()

    @staticmethod
    def create_user_for_tenant(
        db: Session,
        tenant_id: UUID,
        user_in: UserCreate,
        creator_id: Optional[UUID] = None
    ) -> User:
        # Verificar tenant
        TenantService.get_tenant_by_id(db, tenant_id)

        # Verificar unicidad de email dentro del tenant
        existing = db.query(User).filter(
            User.tenant_id == tenant_id,
            User.email == user_in.email.lower().strip()
        ).first()
        if existing:
            raise ConflictException(f"El correo '{user_in.email}' ya está registrado en este despacho")

        user = User(
            tenant_id=tenant_id,
            email=user_in.email.lower().strip(),
            hashed_password=get_password_hash(user_in.password),
            full_name=user_in.full_name.strip(),
            role=user_in.role,
            professional_license=user_in.professional_license.strip() if user_in.professional_license else None
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Audit
        audit = AuditLog(
            tenant_id=tenant_id,
            user_id=creator_id,
            action="CREATE_USER",
            resource_type="USER",
            resource_id=str(user.id),
            details={"email": user.email, "role": user.role}
        )
        db.add(audit)
        db.commit()

        return user

    @staticmethod
    def list_users_by_tenant(db: Session, tenant_id: UUID, skip: int = 0, limit: int = 50) -> List[User]:
        return db.query(User).filter(User.tenant_id == tenant_id).offset(skip).limit(limit).all()
