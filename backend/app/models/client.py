import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class Client(Base):
    """Representa a un cliente del despacho jurídico (Aislamiento por Tenant)."""
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    rfc = Column(String(20), nullable=True, index=True)
    curp = Column(String(20), nullable=True)
    client_type = Column(String(50), nullable=False, default="PERSONA_MORAL")  # PERSONA_FISICA | PERSONA_MORAL
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    tenant = relationship("Tenant", back_populates="clients")
    cases = relationship("Case", back_populates="client", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="client")

    __table_args__ = (
        Index("ix_clients_tenant_name", "tenant_id", "name"),
    )

    def __repr__(self):
        return f"<Client {self.name} ({self.rfc}) Tenant:{self.tenant_id}>"
