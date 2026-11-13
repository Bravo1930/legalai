from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class AlternativeOptionSchema(BaseModel):
    label: str
    text: str


class LegalModificationProposalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    batch_id: UUID
    document_id: UUID
    finding_id: Optional[UUID] = None
    clause_number: Optional[int] = None
    clause_title: str
    problem_explanation: str
    original_text: str
    proposed_text: str
    alternative_options: List[Dict[str, Any]] = []
    missing_data_placeholders: List[str] = []
    legal_foundation: Optional[str] = None
    diff_summary: Optional[str] = None
    status: str
    lawyer_final_text: Optional[str] = None
    lawyer_notes: Optional[str] = None
    reviewed_by_id: Optional[UUID] = None
    reviewer_license: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class ModificationProposalBatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    document_version_id: Optional[UUID] = None
    title: str
    objective: str
    status: str
    total_proposals: int
    accepted_count: int
    rejected_count: int
    pending_count: int
    applied_version_number: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[LegalModificationProposalResponse] = []


class GenerateProposalsRequest(BaseModel):
    title: Optional[str] = None
    objective: str = Field(default="BALANCED", description="BALANCED, CLIENT_PROTECTIVE, STANDARD, CLARITY")
    finding_ids: Optional[List[UUID]] = None


class ReviewProposalItemRequest(BaseModel):
    status: str = Field(..., description="ACCEPTED, REJECTED, MODIFIED_BY_LAWYER")
    lawyer_final_text: Optional[str] = None
    lawyer_notes: Optional[str] = None
    reviewer_license: Optional[str] = None


class CompileNewVersionRequest(BaseModel):
    version_notes: str = Field(..., min_length=5, description="Justificación y resumen de la nueva versión creada")
    reviewer_license: Optional[str] = Field(default=None, description="Cédula profesional del abogado autorizador")
