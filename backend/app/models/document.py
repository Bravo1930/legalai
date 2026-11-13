import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class DocumentClassification:
    CONTRATO = "CONTRATO"
    CONVENIO = "CONVENIO"
    DEMANDA = "DEMANDA"
    CONTESTACION = "CONTESTACION"
    ESCRITO_JUDICIAL = "ESCRITO_JUDICIAL"
    PODER_NOTARIAL = "PODER_NOTARIAL"
    ACTA_ASAMBLEA = "ACTA_ASAMBLEA"
    DOCUMENTO_CORPORATIVO = "DOCUMENTO_CORPORATIVO"
    ANEXO = "ANEXO"
    IDENTIFICACION = "IDENTIFICACION"
    SENTENCIA_ACUERDO = "SENTENCIA_ACUERDO"
    OTRO = "OTRO"

    ALL_TYPES = [
        CONTRATO, CONVENIO, DEMANDA, CONTESTACION, ESCRITO_JUDICIAL,
        PODER_NOTARIAL, ACTA_ASAMBLEA, DOCUMENTO_CORPORATIVO, ANEXO,
        IDENTIFICACION, SENTENCIA_ACUERDO, OTRO
    ]


class Document(Base):
    """Representa el documento jurídico original inmutable (Write-Once-Read-Many)."""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(UUID(as_uuid=True), ForeignKey("cases.id", ondelete="SET NULL"), nullable=True, index=True)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True, index=True)
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    sha256_hash = Column(String(64), nullable=False, index=True)  # Hash inmutable del binario
    storage_path = Column(String(500), nullable=False)
    doc_type = Column(String(50), nullable=False, default=DocumentClassification.CONTRATO, index=True)
    
    is_original = Column(Boolean, default=True, nullable=False)
    is_confidential = Column(Boolean, default=False, nullable=False)
    page_count = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    tenant = relationship("Tenant", back_populates="documents")
    case = relationship("Case", back_populates="documents")
    client = relationship("Client", back_populates="documents")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan", order_by="DocumentVersion.version_number")
    metadata_record = relationship("DocumentMetadata", back_populates="document", uselist=False, cascade="all, delete-orphan")
    approvals = relationship("LegalApproval", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_documents_tenant_sha256", "tenant_id", "sha256_hash"),
        Index("ix_documents_tenant_title", "tenant_id", "title"),
    )

    def __repr__(self):
        return f"<Document {self.title} ({self.doc_type}) SHA:{self.sha256_hash[:8]}>"


class DocumentVersion(Base):
    """Versiones derivadas o modificadas de un documento (sin alterar el original)."""
    __tablename__ = "document_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    version_number = Column(Integer, nullable=False, default=1)
    storage_path = Column(String(500), nullable=False)
    sha256_hash = Column(String(64), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    change_summary = Column(Text, nullable=True)  # Justificación del cambio
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    document = relationship("Document", back_populates="versions")
    created_by = relationship("User")

    __table_args__ = (
        Index("ix_doc_versions_unique", "document_id", "version_number", unique=True),
    )

    def __repr__(self):
        return f"<DocumentVersion v{self.version_number} of Doc:{self.document_id}>"


class DocumentMetadata(Base):
    """Metadatos jurídicos estructurados y texto extraído del documento."""
    __tablename__ = "document_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Metadatos Jurídicos Extraídos
    parties = Column(JSON, nullable=True)             # Listado de partes identificadas
    doc_date = Column(String(50), nullable=True)       # Fecha del instrumento o resolución
    subject_matter = Column(Text, nullable=True)       # Objeto del contrato o materia de litigio
    obligations = Column(JSON, nullable=True)          # Cláusulas u obligaciones clave
    amounts = Column(JSON, nullable=True)              # Montos, divisas, penalidades
    terms_deadlines = Column(JSON, nullable=True)      # Plazos fatales o vigencias
    signers = Column(JSON, nullable=True)              # Nombres y cargos de los firmantes
    jurisdiction = Column(String(100), nullable=True)  # Jurisdicción pactada o legal
    court_authority = Column(String(255), nullable=True) # Juzgado / Autoridad emisora
    procedure_type = Column(String(100), nullable=True)# Tipo de juicio
    references = Column(JSON, nullable=True)           # Leyes citadas, escrituras, etc.
    
    raw_text = Column(Text, nullable=True)             # Texto extraído normalizado
    ocr_applied = Column(Boolean, default=False, nullable=False)
    processing_time_ms = Column(Integer, default=0, nullable=False)
    extracted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    document = relationship("Document", back_populates="metadata_record")

    def __repr__(self):
        return f"<DocumentMetadata for Doc:{self.document_id} OCR:{self.ocr_applied}>"
