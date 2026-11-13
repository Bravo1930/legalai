import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class ProposalBatchStatus:
    PENDING_REVIEW = "PENDING_REVIEW"
    PARTIALLY_ACCEPTED = "PARTIALLY_ACCEPTED"
    FULLY_ACCEPTED = "FULLY_ACCEPTED"
    REJECTED = "REJECTED"
    APPLIED_TO_NEW_VERSION = "APPLIED_TO_NEW_VERSION"


class ProposalItemStatus:
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    MODIFIED_BY_LAWYER = "MODIFIED_BY_LAWYER"


class ModificationProposalBatch(Base):
    """Lote de propuestas de modificación y redacción jurídica para un documento."""
    __tablename__ = "modification_proposal_batches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    title = Column(String(255), nullable=False)
    objective = Column(String(50), default="BALANCED", nullable=False)  # BALANCED, CLIENT_PROTECTIVE, STANDARD, CLARITY
    status = Column(String(50), default=ProposalBatchStatus.PENDING_REVIEW, nullable=False, index=True)

    total_proposals = Column(Integer, default=0, nullable=False)
    accepted_count = Column(Integer, default=0, nullable=False)
    rejected_count = Column(Integer, default=0, nullable=False)
    pending_count = Column(Integer, default=0, nullable=False)

    applied_version_number = Column(Integer, nullable=True)  # Número de la nueva versión creada al aplicar
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    tenant = relationship("Tenant")
    document = relationship("Document")
    created_by = relationship("User", foreign_keys=[created_by_id])
    items = relationship("LegalModificationProposal", back_populates="batch", cascade="all, delete-orphan", order_by="LegalModificationProposal.created_at.asc()")


class LegalModificationProposal(Base):
    """Propuesta granular de modificación de una cláusula o acápite."""
    __tablename__ = "legal_modification_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    batch_id = Column(UUID(as_uuid=True), ForeignKey("modification_proposal_batches.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    finding_id = Column(UUID(as_uuid=True), ForeignKey("legal_findings.id", ondelete="SET NULL"), nullable=True)

    clause_number = Column(Integer, nullable=True)
    clause_title = Column(String(255), nullable=False)

    problem_explanation = Column(Text, nullable=False)
    original_text = Column(Text, nullable=False)
    proposed_text = Column(Text, nullable=False)

    # Opciones alternativas: e.g. [{"label": "Opción Bilateral", "text": "..."}, {"label": "Opción Protectora", "text": "..."}]
    alternative_options = Column(JSON, nullable=False, default=list)

    # Campos faltantes que el abogado debe completar (Regla: no inventar datos)
    # Ej. ["[PENDIENTE: Nombre del Notario]", "[PENDIENTE: Fecha de Inicio]"]
    missing_data_placeholders = Column(JSON, nullable=False, default=list)

    legal_foundation = Column(Text, nullable=True)
    diff_summary = Column(Text, nullable=True)

    status = Column(String(50), default=ProposalItemStatus.PENDING, nullable=False, index=True)
    lawyer_final_text = Column(Text, nullable=True)  # Texto con ajustes hechos por el abogado
    lawyer_notes = Column(Text, nullable=True)       # Observaciones del abogado
    
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_license = Column(String(50), nullable=True)  # Cédula Profesional
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    batch = relationship("ModificationProposalBatch", back_populates="items")
    tenant = relationship("Tenant")
    document = relationship("Document")
    finding = relationship("LegalFinding")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    __table_args__ = (
        Index("ix_modification_proposals_tenant_doc", "tenant_id", "document_id"),
        Index("ix_modification_proposals_status", "status"),
    )
