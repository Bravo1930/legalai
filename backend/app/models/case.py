import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class LegalMatter:
    AMPARO = "AMPARO"
    CIVIL = "CIVIL"
    MERCANTIL = "MERCANTIL"
    PENAL = "PENAL"
    LABORAL = "LABORAL"
    FISCAL = "FISCAL"
    ADMINISTRATIVO = "ADMINISTRATIVO"
    CORPORATIVO = "CORPORATIVO"
    FAMILIAR = "FAMILIAR"
    OTRO = "OTRO"


class CaseStatus:
    ACTIVO = "ACTIVO"
    EN_TRAMITE = "EN_TRAMITE"
    SENTENCIADO = "SENTENCIADO"
    ARCHIVADO = "ARCHIVADO"
    SUSPENDIDO = "SUSPENDIDO"


class Case(Base):
    """Representa un expediente jurídico o asunto corporativo."""
    __tablename__ = "cases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    case_number = Column(String(100), nullable=False, index=True)  # Ej: Exp. 124/2026 o Toca 45/2026
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    matter = Column(String(50), nullable=False, default=LegalMatter.MERCANTIL, index=True)
    jurisdiction = Column(String(50), nullable=False, default="FEDERAL")  # FEDERAL | ESTATAL | CDMX
    state = Column(String(100), nullable=True)                          # Entidad Federativa de México
    court_authority = Column(String(255), nullable=True)                # Ej: Juzgado 3o de Distrito en Materia Civil
    status = Column(String(50), nullable=False, default=CaseStatus.ACTIVO, index=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    tenant = relationship("Tenant", back_populates="cases")
    client = relationship("Client", back_populates="cases")
    lead_lawyer = relationship("User", foreign_keys=[lead_lawyer_id])
    documents = relationship("Document", back_populates="case", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_cases_tenant_number", "tenant_id", "case_number"),
    )

    def __repr__(self):
        return f"<Case {self.case_number}: {self.title} ({self.matter})>"
