import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


class AIAgentType:
    CLASSIFIER = "CLASSIFIER"
    EXTRACTOR = "EXTRACTOR"
    CLAUSE_ANALYST = "CLAUSE_ANALYST"
    RISK_DETECTOR = "RISK_DETECTOR"
    RESEARCHER = "RESEARCHER"
    DRAFTER = "DRAFTER"
    VERIFIER = "VERIFIER"
    FULL_SUITE = "FULL_SUITE"

    ALL_AGENTS = [
        CLASSIFIER, EXTRACTOR, CLAUSE_ANALYST,
        RISK_DETECTOR, RESEARCHER, DRAFTER, VERIFIER, FULL_SUITE
    ]


class AIAnalysis(Base):
    """Registro inmutable de ejecuciones de análisis por agentes de IA con modelos locales."""
    __tablename__ = "ai_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    agent_type = Column(String(50), nullable=False, index=True)
    model_used = Column(String(100), nullable=False)
    
    # Parámetros y auditoría del prompt
    prompt_template = Column(Text, nullable=False)
    input_params = Column(JSON, nullable=True)  # temperature, num_ctx, etc.
    
    # Salida estructurada Pydantic validada
    structured_output = Column(JSON, nullable=False)
    raw_response = Column(Text, nullable=True)

    # Métricas de consumo y rendimiento
    tokens_prompt = Column(Integer, default=0, nullable=False)
    tokens_completion = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    # Relaciones
    tenant = relationship("Tenant")
    document = relationship("Document")
    created_by = relationship("User")

    __table_args__ = (
        Index("ix_ai_analyses_doc_agent", "document_id", "agent_type"),
    )

    def __repr__(self):
        return f"<AIAnalysis {self.agent_type} on Doc:{self.document_id} Model:{self.model_used}>"
