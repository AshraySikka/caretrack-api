import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


# Valid status transitions
VALID_STATUSES = ["draft", "active", "completed", "cancelled"]

VALID_TRANSITIONS = {
    "draft": ["active", "cancelled"],
    "active": ["completed", "cancelled"],
    "completed": [],
    "cancelled": [],
}


class CarePlanCreate(BaseModel):
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    title: str
    description: Optional[str] = None
    goals: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None


class CarePlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    goals: Optional[str] = None
    provider_id: Optional[uuid.UUID] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CarePlanStatusUpdate(BaseModel):
    status: str


class PatientSummary(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    health_card_no: str

    model_config = {"from_attributes": True}


class ProviderSummary(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    provider_type: str

    model_config = {"from_attributes": True}


class CreatorSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class CarePlanResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    created_by: uuid.UUID
    title: str
    description: Optional[str] = None
    goals: Optional[str] = None
    status: str
    start_date: date
    end_date: Optional[date] = None
    patient: Optional[PatientSummary] = None
    provider: Optional[ProviderSummary] = None
    creator: Optional[CreatorSummary] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CarePlanListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    care_plans: list[CarePlanResponse]