import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.users import User
from app.schemas.care_plan import (
    CarePlanCreate,
    CarePlanUpdate,
    CarePlanStatusUpdate,
    CarePlanResponse,
    CarePlanListResponse,
    VALID_STATUSES,
)
from app.services.care_plan_service import (
    get_care_plans,
    get_care_plan_by_id,
    create_care_plan,
    update_care_plan,
    update_care_plan_status,
    delete_care_plan,
)

router = APIRouter(prefix="/api/v1/care-plans", tags=["Care Plans"])


@router.get("/", response_model=CarePlanListResponse)
async def list_care_plans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    patient_id: Optional[uuid.UUID] = Query(None),
    provider_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all care plans with optional filters."""
    return await get_care_plans(db, page, page_size, status, patient_id, provider_id)


@router.post("/", response_model=CarePlanResponse, status_code=201)
async def create_new_care_plan(
    care_plan_data: CarePlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new care plan."""
    care_plan = await create_care_plan(db, care_plan_data, current_user.id)
    return care_plan


@router.get("/{care_plan_id}", response_model=CarePlanResponse)
async def get_care_plan(
    care_plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single care plan by ID."""
    care_plan = await get_care_plan_by_id(db, care_plan_id)
    if not care_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care plan not found",
        )
    return care_plan


@router.put("/{care_plan_id}", response_model=CarePlanResponse)
async def update_existing_care_plan(
    care_plan_id: uuid.UUID,
    care_plan_data: CarePlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a care plan. Not allowed if status is completed or cancelled."""
    care_plan, error = await update_care_plan(db, care_plan_id, care_plan_data)
    if error == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care plan not found",
        )
    if error == "locked":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a completed or cancelled care plan",
        )
    return care_plan


@router.patch("/{care_plan_id}/status", response_model=CarePlanResponse)
async def change_care_plan_status(
    care_plan_id: uuid.UUID,
    status_update: CarePlanStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Change care plan status.
    Valid transitions: draft→active, draft→cancelled,
    active→completed, active→cancelled
    """
    if status_update.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {VALID_STATUSES}",
        )

    care_plan, error = await update_care_plan_status(
        db, care_plan_id, status_update.status
    )
    if error == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care plan not found",
        )
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    return care_plan


@router.delete("/{care_plan_id}", status_code=204)
async def remove_care_plan(
    care_plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a care plan. Only allowed if status is draft."""
    care_plan, error = await delete_care_plan(db, care_plan_id)
    if error == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Care plan not found",
        )
    if error == "only_draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft care plans can be deleted",
        )