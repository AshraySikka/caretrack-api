import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientUpdate


async def get_patient_by_id(db: AsyncSession, patient_id: uuid.UUID):
    """Fetch a single patient by their UUID."""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalars().first()


async def get_patient_by_health_card(db: AsyncSession, health_card_no: str):
    """Fetch a patient by their health card number."""
    result = await db.execute(
        select(Patient).where(Patient.health_card_no == health_card_no)
    )
    return result.scalars().first()


async def get_patients(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    coordinator_id: Optional[uuid.UUID] = None,
):
    """
    List all patients with pagination and optional filters.
    - Filter by status: active, discharged, on_hold
    - Filter by coordinator_id
    """
    query = select(Patient)

    # Apply filters if provided
    if status:
        query = query.where(Patient.status == status)
    if coordinator_id:
        query = query.where(Patient.assigned_coordinator_id == coordinator_id)

    # Get total count for pagination
    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    patients = result.scalars().all()

    return {"total": total, "page": page, "page_size": page_size, "patients": patients}


async def create_patient(db: AsyncSession, patient_data: PatientCreate):
    """Create a new patient record."""
    # Check if health card number already exists
    existing = await get_patient_by_health_card(db, patient_data.health_card_no)
    if existing:
        return None

    new_patient = Patient(
        first_name=patient_data.first_name,
        last_name=patient_data.last_name,
        date_of_birth=patient_data.date_of_birth,
        health_card_no=patient_data.health_card_no,
        phone=patient_data.phone,
        email=patient_data.email,
        address=patient_data.address,
        assigned_coordinator_id=patient_data.assigned_coordinator_id,
    )

    db.add(new_patient)
    await db.flush()
    await db.refresh(new_patient)
    return new_patient


async def update_patient(
    db: AsyncSession, patient_id: uuid.UUID, patient_data: PatientUpdate
):
    """Update an existing patient record."""
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        return None

    # Only update fields that were actually sent
    update_data = patient_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    await db.flush()
    await db.refresh(patient)
    return patient


async def delete_patient(db: AsyncSession, patient_id: uuid.UUID):
    """Soft delete a patient by setting status to discharged."""
    patient = await get_patient_by_id(db, patient_id)
    if not patient:
        return None

    patient.status = "discharged"
    await db.flush()
    return patient