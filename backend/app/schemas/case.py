from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class CaseCreate(BaseModel):
    client_id: UUID
    case_number: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    matter: str = Field("MERCANTIL")
    jurisdiction: str = Field("FEDERAL")
    state: Optional[str] = Field(None, max_length=100)
    court_authority: Optional[str] = Field(None, max_length=255)


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    client_id: UUID
    lead_lawyer_id: Optional[UUID] = None
    case_number: str
    title: str
    description: Optional[str] = None
    matter: str
    jurisdiction: str
    state: Optional[str] = None
    court_authority: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
