import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class RuleCategory:
    MANDATORY_CLAUSE = "MANDATORY_CLAUSE"
    PROHIBITED_CLAUSE = "PROHIBITED_CLAUSE"
    TERM_LIMIT = "TERM_LIMIT"
    AMOUNT_LIMIT = "AMOUNT_LIMIT"
    PENALTY = "PENALTY"
    OBLIGATION = "OBLIGATION"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    DATA_PROTECTION = "DATA_PROTECTION"
    TERMINATION = "TERMINATION"
    JURISDICTION = "JURISDICTION"
    COMPETENCE = "COMPETENCE"
    SIGNATURES = "SIGNATURES"
    LEGAL_REPRESENTATION = "LEGAL_REPRESENTATION"
    POWERS_FACULTIES = "POWERS_FACULTIES"
    COMMERCIAL_REQUIREMENT = "COMMERCIAL_REQUIREMENT"

    ALL_CATEGORIES = [
        MANDATORY_CLAUSE, PROHIBITED_CLAUSE, TERM_LIMIT, AMOUNT_LIMIT,
        PENALTY, OBLIGATION, CONFIDENTIALITY, DATA_PROTECTION,
        TERMINATION, JURISDICTION, COMPETENCE, SIGNATURES,
        LEGAL_REPRESENTATION, POWERS_FACULTIES, COMMERCIAL_REQUIREMENT
    ]


class RuleSeverity:
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    ALL_SEVERITIES = [CRITICAL, HIGH, MEDIUM, LOW, INFO]


class RuleOperator:
    CONTAINS_ALL_KEYWORDS = "CONTAINS_ALL_KEYWORDS"
    CONTAINS_ANY_KEYWORD = "CONTAINS_ANY_KEYWORD"
    PROHIBITS_KEYWORDS = "PROHIBITS_KEYWORDS"
    REGEX_MATCH = "REGEX_MATCH"
    NUMERIC_RANGE = "NUMERIC_RANGE"
    METADATA_EQUALS = "METADATA_EQUALS"
    METADATA_EXISTS = "METADATA_EXISTS"

    ALL_OPERATORS = [
        CONTAINS_ALL_KEYWORDS, CONTAINS_ANY_KEYWORD, PROHIBITS_KEYWORDS,
        REGEX_MATCH, NUMERIC_RANGE, METADATA_EQUALS, METADATA_EXISTS
    ]


class RuleEvaluationStatus:
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PENDING_HUMAN_REVIEW = "PENDING_HUMAN_REVIEW"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class LegalRule(Base):
    """Regla jurídica determinista configurable por organización o cliente."""
    __tablename__ = "legal_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    rule_code = Column(String(50), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False, default=RuleCategory.MANDATORY_CLAUSE, index=True)
    severity = Column(String(20), nullable=False, default=RuleSeverity.CRITICAL, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Ámbito de aplicación (Scope)
    # Formato: {"doc_types": ["CONTRATO"], "client_ids": [...], "legal_matters": ["MERCANTIL"], "jurisdictions": ["CDMX"]}
    scope = Column(JSON, nullable=False, default=dict)

    # Definición de la condición determinista
    # Formato: {"operator": "CONTAINS_ALL_KEYWORDS", "parameters": {"keywords": ["jurisdicción", "ciudad de méxico"]}}
    condition_definition = Column(JSON, nullable=False, default=dict)

    expected_outcome = Column(Text, nullable=False)
    legal_foundation = Column(Text, nullable=True)  # Ej. "Art. 1093 Código de Comercio"

    version = Column(Integer, default=1, nullable=False)
    effective_from = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    effective_until = Column(DateTime(timezone=True), nullable=True)

    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    responsible_lawyer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    tenant = relationship("Tenant")
    created_by = relationship("User", foreign_keys=[created_by_id])
    responsible_lawyer = relationship("User", foreign_keys=[responsible_lawyer_id])
    versions = relationship("RuleVersion", back_populates="rule", cascade="all, delete-orphan", order_by="desc(RuleVersion.version_number)")
    evaluations_detail = relationship("RuleEvaluationDetail", back_populates="rule")

    __table_args__ = (
        Index("ix_legal_rules_tenant_code", "tenant_id", "rule_code", unique=True),
        Index("ix_legal_rules_tenant_cat", "tenant_id", "category"),
    )

    def __repr__(self):
        return f"<LegalRule {self.rule_code}: {self.name} v{self.version}>"


class RuleVersion(Base):
    """Historial inmutable de versiones de reglas deterministas."""
    __tablename__ = "rule_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("legal_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    scope = Column(JSON, nullable=False)
    condition_definition = Column(JSON, nullable=False)
    expected_outcome = Column(Text, nullable=False)
    legal_foundation = Column(Text, nullable=True)

    change_reason = Column(Text, nullable=True)
    modified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relaciones
    rule = relationship("LegalRule", back_populates="versions")
    modified_by = relationship("User", foreign_keys=[modified_by_id])

    __table_args__ = (
        Index("ix_rule_versions_rule_ver", "rule_id", "version_number", unique=True),
    )


class RuleAuditLog(Base):
    """Pista de auditoría para creaciones, modificaciones y cambios de estado de reglas."""
    __tablename__ = "rule_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("legal_rules.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, ACTIVATE, DEACTIVATE, ARCHIVE
    diff_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    rule = relationship("LegalRule")
    tenant = relationship("Tenant")
    user = relationship("User")


class RuleEvaluation(Base):
    """Resultado maestro de la evaluación determinista de un documento."""
    __tablename__ = "rule_evaluations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True)
    evaluated_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    total_rules_evaluated = Column(Integer, default=0, nullable=False)
    passed_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    pending_count = Column(Integer, default=0, nullable=False)
    not_applicable_count = Column(Integer, default=0, nullable=False)

    # Score de cumplimiento determinista: (passed / (total - not_applicable)) * 100
    compliance_score = Column(Float, default=0.0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relaciones
    tenant = relationship("Tenant")
    document = relationship("Document")
    document_version = relationship("DocumentVersion")
    evaluated_by = relationship("User")
    details = relationship("RuleEvaluationDetail", back_populates="evaluation", cascade="all, delete-orphan")


class RuleEvaluationDetail(Base):
    """Detalle línea por línea de cada regla determinista evaluada contra el documento."""
    __tablename__ = "rule_evaluation_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("rule_evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("legal_rules.id", ondelete="SET NULL"), nullable=True, index=True)

    rule_code = Column(String(50), nullable=False)
    rule_name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)

    # COMPLIANT, NON_COMPLIANT, PENDING_HUMAN_REVIEW, NOT_APPLICABLE
    status = Column(String(30), nullable=False, index=True)

    matched_evidence = Column(Text, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # Revisión humana (HITL) para observaciones pendientes
    human_verification_notes = Column(Text, nullable=True)
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relaciones
    evaluation = relationship("RuleEvaluation", back_populates="details")
    rule = relationship("LegalRule", back_populates="evaluations_detail")
    verified_by = relationship("User", foreign_keys=[verified_by_id])
