import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class TaskStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Task(Base):
    """Representa una tarea asíncrona (OCR, indexación vectorial, análisis de IA)."""
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String(100), nullable=False, index=True)  # OCR_EXTRACTION, EMBEDDING_INGESTION, CONTRACT_ANALYSIS
    status = Column(String(50), nullable=False, default=TaskStatus.PENDING, index=True)
    payload = Column(JSON, nullable=True)                       # Parámetros de entrada
    result = Column(JSON, nullable=True)                        # Resultado estructurado
    error_message = Column(Text, nullable=True)                 # Detalle si falló
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    tenant = relationship("Tenant", back_populates="tasks")

    def __repr__(self):
        return f"<Task {self.task_type} [{self.status}] Tenant:{self.tenant_id}>"
