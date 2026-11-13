from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class ClientCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    rfc: Optional[str] = Field(None, max_length=20)
    curp: Optional[str] = Field(None, max_length=20)
    client_type: str = Field("PERSONA_MORAL")  # PERSONA_FISICA | PERSONA_MORAL
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    rfc: Optional[str] = None
    curp: Optional[str] = None
    client_type: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    updated_at: datetime
