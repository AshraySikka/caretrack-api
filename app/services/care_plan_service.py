import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.care_plan import CarePlan
from app.schemas.care_plan import CarePlanCreate, CarePlanUpdate, VALID_TRANSITIONS


async def get_care_plan_by_id(db: AsyncSession, care_plan_id: uuid.UUID):
    """Fetch a single care plan by UUID."""
    result = await db.execute(
        select(CarePlan).where(CarePlan.id == care_plan_id)
    )
    return result.scalars().first()


async def get_care_plans(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    patient_id: Optional[uuid.UUID] = None,
    provider_id: Optional[uuid.UUID] = None,
):
    """List all care plans with pagination and optional filters."""
    query = select(CarePlan)

    if status:
        query = query.where(CarePlan.status == status)
    if patient_id:
        query = query.where(CarePlan.patient_id == patient_id)
    if provider_id:
        query = query.where(CarePlan.provider_id == provider_id)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    care_plans = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "care_plans": care_plans,
    }


async def create_care_plan(
    db: AsyncSession,
    care_plan_data: CarePlanCreate,
    created_by: uuid.UUID,
):
    """Create a new care plan."""
    new_care_plan = CarePlan(
        patient_id=care_plan_data.patient_id,
        provider_id=care_plan_data.provider_id,
        created_by=created_by,
        title=care_plan_data.title,
        description=care_plan_data.description,
        goals=care_plan_data.goals,
        start_date=care_plan_data.start_date,
        end_date=care_plan_data.end_date,
    )

    db.add(new_care_plan)
    await db.flush()
    await db.refresh(new_care_plan)
    return new_care_plan


async def update_care_plan(
    db: AsyncSession,
    care_plan_id: uuid.UUID,
    care_plan_data: CarePlanUpdate,
):
    """Update an existing care plan."""
    care_plan = await get_care_plan_by_id(db, care_plan_id)
    if not care_plan:
        return None, "not_found"

    # Cannot update a completed or cancelled care plan
    if care_plan.status in ["completed", "cancelled"]:
        return None, "locked"

    update_data = care_plan_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(care_plan, field, value)

    await db.flush()
    await db.refresh(care_plan)
    return care_plan, None


async def update_care_plan_status(
    db: AsyncSession,
    care_plan_id: uuid.UUID,
    new_status: str,
):
    """
    Update care plan status with transition validation.
    Only allows valid transitions defined in VALID_TRANSITIONS.
    """
    care_plan = await get_care_plan_by_id(db, care_plan_id)
    if not care_plan:
        return None, "not_found"

    allowed = VALID_TRANSITIONS.get(care_plan.status, [])
    if new_status not in allowed:
        return None, f"Cannot transition from '{care_plan.status}' to '{new_status}'"

    care_plan.status = new_status
    await db.flush()
    await db.refresh(care_plan)
    return care_plan, None


async def delete_care_plan(db: AsyncSession, care_plan_id: uuid.UUID):
    """Delete a care plan — only allowed if status is draft."""
    care_plan = await get_care_plan_by_id(db, care_plan_id)
    if not care_plan:
        return None, "not_found"

    if care_plan.status != "draft":
        return None, "only_draft"

    await db.delete(care_plan)
    await db.flush()
    return care_plan, None