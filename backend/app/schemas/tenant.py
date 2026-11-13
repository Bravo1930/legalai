from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    rfc: Optional[str] = Field(None, max_length=20)
    contact_email: EmailStr


class TenantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    rfc: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[EmailStr] = None
    is_active: Optional[bool] = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    rfc: Optional[str] = None
    contact_email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
