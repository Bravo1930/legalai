import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class FindingIssueType:
    CONTRADICTION = "CONTRADICTION"
    OMISSION = "OMISSION"
    EXCESSIVE_PENALTY = "EXCESSIVE_PENALTY"
    UNBALANCED_OBLIGATION = "UNBALANCED_OBLIGATION"
    AMBIGUITY = "AMBIGUITY"
    JURISDICTION_CONFLICT = "JURISDICTION_CONFLICT"
    DATA_PROTECTION_DEFECT = "DATA_PROTECTION_DEFECT"
    MISSING_REPRESENTATION = "MISSING_REPRESENTATION"
    UNVERIFIED_CITATION = "UNVERIFIED_CITATION"
    COMPLIANCE_BREACH = "COMPLIANCE_BREACH"
    TERM_UNCERTAINTY = "TERM_UNCERTAINTY"
    OTHER = "OTHER"

    ALL_ISSUES = [
        CONTRADICTION, OMISSION, EXCESSIVE_PENALTY, UNBALANCED_OBLIGATION,
        AMBIGUITY, JURISDICTION_CONFLICT, DATA_PROTECTION_DEFECT,
        MISSING_REPRESENTATION, UNVERIFIED_CITATION, COMPLIANCE_BREACH,
        TERM_UNCERTAINTY, OTHER
    ]


class FindingSeverity:
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NO_OBSERVATIONS = "NO_OBSERVATIONS"
    REQUIRES_HUMAN_VALIDATION = "REQUIRES_HUMAN_VALIDATION"

    ALL_SEVERITIES = [
        CRITICAL, HIGH, MEDIUM, LOW, NO_OBSERVATIONS, REQUIRES_HUMAN_VALIDATION
    ]


class FindingReviewStatus:
    PENDING_REVIEW = "PENDING_REVIEW"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    MODIFIED = "MODIFIED"


class AdvancedAnalysisSession(Base):
    """Sesión maestra de análisis jurídico documental avanzado."""
    __tablename__ = "advanced_analysis_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    overall_risk_score = Column(Float, default=0.0, nullable=False)  # 0 a 100
    overall_severity = Column(String(50), default=FindingSeverity.LOW, nullable=False)
    
    findings_count = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    high_count = Column(Integer, default=0, nullable=False)
    medium_count = Column(Integer, default=0, nullable=False)
    low_count = Column(Integer, default=0, nullable=False)
    pending_review_count = Column(Integer, default=0, nullable=False)

    summary = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relaciones
    tenant = relationship("Tenant")
    document = relationship("Document")
    created_by = relationship("User", foreign_keys=[created_by_id])
    findings = relationship("LegalFinding", back_populates="session", cascade="all, delete-orphan", order_by="desc(LegalFinding.severity)")
    clauses = relationship("ClauseDecomposition", back_populates="session", cascade="all, delete-orphan", order_by="ClauseDecomposition.clause_number.asc()")


class LegalFinding(Base):
    """Observación jurídica individual estructurada, explicable y verificable."""
    __tablename__ = "legal_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("advanced_analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    finding_code = Column(String(50), nullable=False, index=True)  # Ej. OBS-2026-001
    issue_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=False, index=True)  # CRITICAL, HIGH, MEDIUM, LOW, REQUIRES_HUMAN_VALIDATION

    # Fragmento y localización exacta
    original_fragment = Column(Text, nullable=True)  # Cita textual entrecomillada
    location = Column(String(255), nullable=True)     # Párrafo, página o acápite
    clause_ref = Column(String(255), nullable=True)   # Nombre o número de cláusula

    # Enlace con reglas internas deterministas
    related_rule_code = Column(String(50), nullable=True, index=True)

    # Fundamento normativo verificado (México)
    # Formato: {
    #   "disposition_name": "Código de Comercio", "article": "1093", "jurisdiction": "Federal",
    #   "publication_reform_date": "28-03-2018", "validity_status": "VIGENTE_VERIFICADA" | "REQUIERE_INVESTIGACION_JURIDICA",
    #   "official_source": "DOF / Cámara de Diputados", "query_date": "2026-11-12",
    #   "is_verified": true
    # }
    legal_foundation = Column(JSON, nullable=True)

    risk_explanation = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)

    confidence_score = Column(Float, default=1.0, nullable=False)  # 0.0 a 1.0
    confidence_level = Column(String(20), default="HIGH", nullable=False)  # HIGH, MEDIUM, LOW

    # Human-in-the-Loop (HITL)
    review_status = Column(String(50), default=FindingReviewStatus.PENDING_REVIEW, nullable=False, index=True)
    reviewed_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_license = Column(String(50), nullable=True)   # Cédula profesional
    reviewer_notes = Column(Text, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    session = relationship("AdvancedAnalysisSession", back_populates="findings")
    tenant = relationship("Tenant")
    document = relationship("Document")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    __table_args__ = (
        Index("ix_legal_findings_tenant_doc", "tenant_id", "document_id"),
    )


class ClauseDecomposition(Base):
    """Descomposición estructurada de cada cláusula del documento."""
    __tablename__ = "clause_decompositions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("advanced_analysis_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    clause_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)

    obligations = Column(JSON, nullable=False, default=list)  # [{"party": "...", "description": "..."}]
    rights = Column(JSON, nullable=False, default=list)       # [{"party": "...", "description": "..."}]
    deadlines = Column(JSON, nullable=False, default=list)    # [{"term_days": 15, "trigger": "..."}]
    penalties = Column(JSON, nullable=False, default=list)    # [{"type": "...", "amount": "..."}]

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("AdvancedAnalysisSession", back_populates="clauses")
    document = relationship("Document")


class VersionComparison(Base):
    """Comparación analítica entre dos versiones de un documento (Redline & Risk Delta)."""
    __tablename__ = "version_comparisons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)

    base_version_label = Column(String(100), nullable=False)      # Ej. "Versión 1 (Original)"
    compare_version_label = Column(String(100), nullable=False)   # Ej. "Versión 2 (Revisada)"

    added_clauses = Column(JSON, nullable=False, default=list)
    removed_clauses = Column(JSON, nullable=False, default=list)
    modified_clauses = Column(JSON, nullable=False, default=list)

    # Delta de riesgos: riesgos resueltos vs nuevos riesgos introducidos
    risk_delta = Column(JSON, nullable=False, default=dict)
    summary = Column(Text, nullable=False)

    compared_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    tenant = relationship("Tenant")
    document = relationship("Document")
    compared_by = relationship("User", foreign_keys=[compared_by_id])
