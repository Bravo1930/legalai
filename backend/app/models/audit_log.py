import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class AuditLog(Base):
    """Registro inmutable (Append-Only) para trazabilidad forense de cada operación."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # LOGIN, UPLOAD_DOC, AI_ANALYSIS, HITL_APPROVAL, etc.
    resource_type = Column(String(100), nullable=False)        # DOCUMENT, CASE, USER, TENANT
    resource_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)                     # Metadatos del evento en JSON
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relaciones
    tenant = relationship("Tenant", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog {self.action} on {self.resource_type}:{self.resource_id} by User:{self.user_id}>"
