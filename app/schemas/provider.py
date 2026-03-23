import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class ProviderCreate(BaseModel):
    first_name: str
    last_name: str
    provider_type: str
    license_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    max_patients: int = 20


class ProviderUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    provider_type: Optional[str] = None
    license_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    max_patients: Optional[int] = None
    is_available: Optional[bool] = None


class ProviderResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    provider_type: str
    license_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    max_patients: int
    is_available: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProviderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    providers: list[ProviderResponse]