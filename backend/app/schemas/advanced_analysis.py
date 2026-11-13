from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class LegalFoundationSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disposition_name: str
    article: Optional[str] = None
    jurisdiction: str
    publication_reform_date: str
    validity_status: str  # VIGENTE_VERIFICADA | REQUIERE_INVESTIGACION_JURIDICA
    official_source: str
    query_date: str
    is_verified: bool
    verification_note: Optional[str] = None


class LegalFindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    finding_code: str
    issue_type: str
    title: str
    description: str
    severity: str
    original_fragment: Optional[str] = None
    location: Optional[str] = None
    clause_ref: Optional[str] = None
    related_rule_code: Optional[str] = None
    legal_foundation: Optional[Dict[str, Any]] = None
    risk_explanation: str
    recommendation: str
    confidence_score: float
    confidence_level: str
    review_status: str
    reviewed_by_id: Optional[UUID] = None
    reviewer_license: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class ClauseDecompositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    clause_number: int
    title: str
    raw_text: str
    summary: str
    obligations: List[Any] = []
    rights: List[Any] = []
    deadlines: List[Any] = []
    penalties: List[Any] = []


class AdvancedAnalysisSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    overall_risk_score: float
    overall_severity: str
    findings_count: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    pending_review_count: int
    summary: Optional[str] = None
    execution_time_ms: int
    created_at: datetime
    findings: List[LegalFindingResponse] = []
    clauses: List[ClauseDecompositionResponse] = []


class FindingReviewRequest(BaseModel):
    review_status: str = Field(..., description="VALIDATED, REJECTED, MODIFIED")
    reviewer_license: Optional[str] = Field(default=None, description="Cédula Profesional")
    reviewer_notes: str = Field(..., min_length=3, description="Observaciones jurídicas o dictamen")


class VersionComparisonRequest(BaseModel):
    base_text: str = Field(..., min_length=10)
    compare_text: str = Field(..., min_length=10)
    base_label: str = Field(default="Versión Base (Original)")
    compare_label: str = Field(default="Versión Comparada (Revisada)")


class VersionComparisonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    base_version_label: str
    compare_version_label: str
    added_clauses: List[Dict[str, Any]] = []
    removed_clauses: List[Dict[str, Any]] = []
    modified_clauses: List[Dict[str, Any]] = []
    risk_delta: Dict[str, Any] = {}
    summary: str
    created_at: datetime
