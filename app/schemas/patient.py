import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    health_card_no: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    assigned_coordinator_id: Optional[uuid.UUID] = None


class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    status: Optional[str] = None
    assigned_coordinator_id: Optional[uuid.UUID] = None


class CoordinatorSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class PatientResponse(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    date_of_birth: date
    health_card_no: str
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    status: str
    assigned_coordinator_id: Optional[uuid.UUID] = None
    coordinator: Optional[CoordinatorSummary] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatientListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    patients: list[PatientResponse]