import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

VALID_VISIT_TYPES = [
    "initial_assessment",
    "follow_up",
    "medication",
    "therapy",
]

VALID_STATUSES = ["scheduled", "completed", "cancelled", "no_show"]


class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    care_plan_id: Optional[uuid.UUID] = None
    scheduled_at: datetime
    duration_mins: int = 60
    visit_type: str
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    duration_mins: Optional[int] = None
    visit_type: Optional[str] = None
    notes: Optional[str] = None
    provider_id: Optional[uuid.UUID] = None


class AppointmentStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None


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


class CarePlanSummary(BaseModel):
    id: uuid.UUID
    title: str
    status: str

    model_config = {"from_attributes": True}


class AppointmentResponse(BaseModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    provider_id: uuid.UUID
    care_plan_id: Optional[uuid.UUID] = None
    scheduled_at: datetime
    duration_mins: int
    visit_type: str
    status: str
    notes: Optional[str] = None
    patient: Optional[PatientSummary] = None
    provider: Optional[ProviderSummary] = None
    care_plan: Optional[CarePlanSummary] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AppointmentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    appointments: list[AppointmentResponse]