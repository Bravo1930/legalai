import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class ApprovalStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"


class LegalApproval(Base):
    """Registro de validación humana obligatoria (HITL) con firma y cédula profesional."""
    __tablename__ = "legal_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    status = Column(String(50), nullable=False, default=ApprovalStatus.PENDING, index=True)
    professional_license = Column(String(50), nullable=True)  # Cédula Profesional del abogado que aprueba
    reviewer_name = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)                      # Dictamen u observaciones del abogado
    approved_hash = Column(String(64), nullable=True)        # Hash del documento al momento de aprobar
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    document = relationship("Document", back_populates="approvals")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self):
        return f"<LegalApproval Doc:{self.document_id} [{self.status}] by {self.reviewer_name}>"
