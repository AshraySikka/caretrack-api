import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.users import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatusUpdate,
    AppointmentResponse,
    AppointmentListResponse,
    VALID_STATUSES,
    VALID_VISIT_TYPES,
)
from app.services.appointment_service import (
    get_appointments,
    get_appointment_by_id,
    get_upcoming_appointments,
    create_appointment,
    update_appointment,
    update_appointment_status,
)

router = APIRouter(prefix="/api/v1/appointments", tags=["Appointments"])


@router.get("/upcoming", response_model=list[AppointmentResponse])
async def list_upcoming_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all scheduled appointments in the next 7 days."""
    return await get_upcoming_appointments(db)


@router.get("/", response_model=AppointmentListResponse)
async def list_appointments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    patient_id: Optional[uuid.UUID] = Query(None),
    provider_id: Optional[uuid.UUID] = Query(None),
    date_from: Optional[datetime] = Query(None, description="Filter from date"),
    date_to: Optional[datetime] = Query(None, description="Filter to date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all appointments with optional filters."""
    return await get_appointments(
        db, page, page_size, status, patient_id, provider_id, date_from, date_to
    )


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_new_appointment(
    appointment_data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Schedule a new appointment."""
    if appointment_data.visit_type not in VALID_VISIT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid visit type. Must be one of: {VALID_VISIT_TYPES}",
        )
    appointment, error = await create_appointment(db, appointment_data)
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    return appointment


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single appointment by ID."""
    appointment = await get_appointment_by_id(db, appointment_id)
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_existing_appointment(
    appointment_id: uuid.UUID,
    appointment_data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an appointment. Not allowed if completed, cancelled, or no_show."""
    appointment, error = await update_appointment(db, appointment_id, appointment_data)
    if error == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    if error == "locked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a completed, cancelled, or no_show appointment",
        )
    return appointment


@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
async def change_appointment_status(
    appointment_id: uuid.UUID,
    status_update: AppointmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update appointment status.
    Valid statuses: scheduled, completed, cancelled, no_show
    """
    if status_update.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {VALID_STATUSES}",
        )
    appointment, error = await update_appointment_status(
        db, appointment_id, status_update.status, status_update.notes
    )
    if error == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found",
        )
    if error == "locked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a completed, cancelled, or no_show appointment",
        )
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    return appointment