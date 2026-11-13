from datetime import datetime
from typing import List, Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DocumentMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    parties: Optional[List[Dict[str, Any]]] = None
    doc_date: Optional[str] = None
    subject_matter: Optional[str] = None
    obligations: Optional[List[Any]] = None
    amounts: Optional[List[str]] = None
    terms_deadlines: Optional[List[str]] = None
    signers: Optional[List[Dict[str, Any]]] = None
    jurisdiction: Optional[str] = None
    court_authority: Optional[str] = None
    procedure_type: Optional[str] = None
    references: Optional[List[Any]] = None
    ocr_applied: bool = False
    processing_time_ms: int = 0
    extracted_at: datetime


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    sha256_hash: str
    file_size_bytes: int
    change_summary: Optional[str] = None
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    case_id: Optional[UUID] = None
    client_id: Optional[UUID] = None
    title: str
    filename: str
    file_size_bytes: int
    mime_type: str
    sha256_hash: str
    doc_type: str
    is_original: bool
    is_confidential: bool
    page_count: int
    created_at: datetime
    updated_at: datetime
    metadata_record: Optional[DocumentMetadataResponse] = None
    versions: List[DocumentVersionResponse] = []


class DocumentPreviewResponse(BaseModel):
    id: UUID
    title: str
    filename: str
    doc_type: str
    sha256_hash: str
    page_count: int
    raw_text: str
    metadata: Optional[DocumentMetadataResponse] = None


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
