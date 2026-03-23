import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.provider import Provider
from app.schemas.provider import ProviderCreate, ProviderUpdate


async def get_provider_by_id(db: AsyncSession, provider_id: uuid.UUID):
    """Fetch a single provider by their UUID."""
    result = await db.execute(
        select(Provider).where(Provider.id == provider_id)
    )
    return result.scalars().first()


async def get_provider_by_email(db: AsyncSession, email: str):
    """Fetch a provider by their email address."""
    result = await db.execute(
        select(Provider).where(Provider.email == email)
    )
    return result.scalars().first()


async def get_providers(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    provider_type: Optional[str] = None,
    is_available: Optional[bool] = None,
):
    """List all providers with pagination and optional filters."""
    query = select(Provider)

    if provider_type:
        query = query.where(Provider.provider_type == provider_type)
    if is_available is not None:
        query = query.where(Provider.is_available == is_available)

    count_result = await db.execute(
        select(func.count()).select_from(query.subquery())
    )
    total = count_result.scalar()

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    providers = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "providers": providers,
    }


async def create_provider(db: AsyncSession, provider_data: ProviderCreate):
    """Create a new provider."""
    if provider_data.email:
        existing = await get_provider_by_email(db, provider_data.email)
        if existing:
            return None

    new_provider = Provider(
        first_name=provider_data.first_name,
        last_name=provider_data.last_name,
        provider_type=provider_data.provider_type,
        license_number=provider_data.license_number,
        phone=provider_data.phone,
        email=provider_data.email,
        max_patients=provider_data.max_patients,
    )

    db.add(new_provider)
    await db.flush()
    await db.refresh(new_provider)
    return new_provider


async def update_provider(
    db: AsyncSession, provider_id: uuid.UUID, provider_data: ProviderUpdate
):
    """Update an existing provider."""
    provider = await get_provider_by_id(db, provider_id)
    if not provider:
        return None

    update_data = provider_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)

    await db.flush()
    await db.refresh(provider)
    return provider