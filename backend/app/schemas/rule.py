from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class RuleScopeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    doc_types: List[str] = Field(default_factory=lambda: ["*"], description="Tipos documentales aplicables: CONTRATO, CONVENIO, etc.")
    client_ids: Optional[List[UUID]] = Field(default=None, description="Clientes específicos a los que aplica")
    legal_matters: Optional[List[str]] = Field(default=None, description="Materias jurídicas: MERCANTIL, CIVIL, etc.")
    jurisdictions: Optional[List[str]] = Field(default=None, description="Jurisdicciones aplicables: CDMX, FEDERAL, etc.")


class RuleConditionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operator: str = Field(..., description="CONTAINS_ALL_KEYWORDS, CONTAINS_ANY_KEYWORD, PROHIBITS_KEYWORDS, REGEX_MATCH, NUMERIC_RANGE, METADATA_EQUALS, METADATA_EXISTS")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="keywords, regex_pattern, min_value, max_value, target_field, case_sensitive, etc.")


class LegalRuleBase(BaseModel):
    rule_code: str = Field(..., min_length=2, max_length=50, description="Código identificador único (ej. REG-JUR-001)")
    name: str = Field(..., min_length=3, max_length=255, description="Nombre descriptivo de la regla")
    description: str = Field(..., min_length=5, description="Explicación del criterio de revisión")
    category: str = Field(..., description="Categoría de regla (RuleCategory)")
    severity: str = Field(default="CRITICAL", description="CRITICAL, HIGH, MEDIUM, LOW, INFO")
    scope: RuleScopeSchema = Field(default_factory=RuleScopeSchema)
    condition_definition: RuleConditionSchema = Field(...)
    expected_outcome: str = Field(..., description="Resultado esperado redactado jurídicamente")
    legal_foundation: Optional[str] = Field(default=None, description="Fundamento legal o normativo")
    responsible_lawyer_id: Optional[UUID] = None
    effective_until: Optional[datetime] = None


class LegalRuleCreate(LegalRuleBase):
    pass


class LegalRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    scope: Optional[RuleScopeSchema] = None
    condition_definition: Optional[RuleConditionSchema] = None
    expected_outcome: Optional[str] = None
    legal_foundation: Optional[str] = None
    responsible_lawyer_id: Optional[UUID] = None
    effective_until: Optional[datetime] = None
    change_reason: str = Field(..., min_length=5, description="Motivo obligatorio del cambio para auditoría y versionado")


class RuleStatusToggle(BaseModel):
    is_active: bool
    reason: Optional[str] = None


class RuleVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    name: str
    description: str
    category: str
    severity: str
    scope: Dict[str, Any]
    condition_definition: Dict[str, Any]
    expected_outcome: str
    legal_foundation: Optional[str] = None
    change_reason: Optional[str] = None
    modified_by_id: Optional[UUID] = None
    created_at: datetime


class LegalRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    rule_code: str
    name: str
    description: str
    category: str
    severity: str
    is_active: bool
    scope: Dict[str, Any]
    condition_definition: Dict[str, Any]
    expected_outcome: str
    legal_foundation: Optional[str] = None
    version: int
    effective_from: datetime
    effective_until: Optional[datetime] = None
    created_by_id: Optional[UUID] = None
    responsible_lawyer_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    versions: Optional[List[RuleVersionResponse]] = None


class RuleEvaluationDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_id: UUID
    rule_id: Optional[UUID] = None
    rule_code: str
    rule_name: str
    category: str
    severity: str
    status: str
    matched_evidence: Optional[str] = None
    failure_reason: Optional[str] = None
    human_verification_notes: Optional[str] = None
    verified_by_id: Optional[UUID] = None
    verified_at: Optional[datetime] = None


class RuleEvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    document_id: UUID
    document_version_id: Optional[UUID] = None
    evaluated_by_id: Optional[UUID] = None
    total_rules_evaluated: int
    passed_count: int
    failed_count: int
    pending_count: int
    not_applicable_count: int
    compliance_score: float
    created_at: datetime
    details: List[RuleEvaluationDetailResponse] = []


class RuleVerificationRequest(BaseModel):
    status: str = Field(..., description="COMPLIANT o NON_COMPLIANT")
    notes: str = Field(..., min_length=3, description="Justificación jurídica del abogado")
