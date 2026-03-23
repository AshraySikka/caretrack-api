import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.appointment import Appointment
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    VALID_STATUSES,
    VALID_VISIT_TYPES,
)


async def get_appointment_by_id(db: AsyncSession, appointment_id: uuid.UUID):
    """Fetch a single appointment by UUID."""
    result = await db.execute(
        select(Appointment).where(Appointment.id == appointment_id)
    )
    return result.scalars().first()


async def get_appointments(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    patient_id: Optional[uuid.UUID] = None,
    provider_id: Optional[uuid.UUID] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
):
    """List appointments with pagination and optional filters."""
    query = select(Appointment)

    if status:
        query = query.where(Appointment.status == status)
    if patient_id:
        query = query.where(Appointment.patient_id == patient_id)
    if provider_id:
        query = query.where(Appointment.provider_id == provider_id)
    if date_from:
        query = query.where(Appointment.scheduled_at >= date_from)
    if date_to:
        query = query.where(Appointment.scheduled_at <= date_to)

    query = query.order_by(Appointment.scheduled_at)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    appointments = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "appointments": appointments,
    }


async def get_upcoming_appointments(db: AsyncSession):
    """Get all appointments scheduled in the next 7 days."""
    
    now = datetime.now(timezone.utc)
    seven_days_later = now + timedelta(days=7)

    result = await db.execute(
        select(Appointment)
        .where(Appointment.scheduled_at >= now)
        .where(Appointment.scheduled_at <= seven_days_later)
        .where(Appointment.status == "scheduled")
        .order_by(Appointment.scheduled_at)
    )
    return result.scalars().all()


async def create_appointment(
    db: AsyncSession,
    appointment_data: AppointmentCreate,
):
    """Create a new appointment."""
    if appointment_data.visit_type not in VALID_VISIT_TYPES:
        return None, f"Invalid visit type. Must be one of: {VALID_VISIT_TYPES}"

    new_appointment = Appointment(
        patient_id=appointment_data.patient_id,
        provider_id=appointment_data.provider_id,
        care_plan_id=appointment_data.care_plan_id,
        scheduled_at=appointment_data.scheduled_at,
        duration_mins=appointment_data.duration_mins,
        visit_type=appointment_data.visit_type,
        notes=appointment_data.notes,
    )

    db.add(new_appointment)
    await db.flush()
    await db.refresh(new_appointment)
    return new_appointment, None


async def update_appointment(
    db: AsyncSession,
    appointment_id: uuid.UUID,
    appointment_data: AppointmentUpdate,
):
    """Update an existing appointment."""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        return None, "not_found"

    if appointment.status in ["completed", "cancelled", "no_show"]:
        return None, "locked"

    update_data = appointment_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(appointment, field, value)

    await db.flush()
    await db.refresh(appointment)
    return appointment, None


async def update_appointment_status(
    db: AsyncSession,
    appointment_id: uuid.UUID,
    new_status: str,
    notes: Optional[str] = None,
):
    """Update appointment status."""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        return None, "not_found"

    if new_status not in VALID_STATUSES:
        return None, f"Invalid status. Must be one of: {VALID_STATUSES}"

    if appointment.status in ["completed", "cancelled", "no_show"]:
        return None, "locked"

    appointment.status = new_status
    if notes:
        appointment.notes = notes

    await db.flush()
    await db.refresh(appointment)
    return appointment, None