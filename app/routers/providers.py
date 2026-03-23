import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, get_admin_user
from app.models.users import User
from app.schemas.provider import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    ProviderListResponse,
)
from app.services.provider_service import (
    get_providers,
    get_provider_by_id,
    create_provider,
    update_provider,
)

router = APIRouter(prefix="/api/v1/providers", tags=["Providers"])


@router.get("/", response_model=ProviderListResponse)
async def list_providers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    provider_type: Optional[str] = Query(None, description="Filter by type e.g. RN, PSW, PT"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all providers with optional filters."""
    return await get_providers(db, page, page_size, provider_type, is_available)


@router.post("/", response_model=ProviderResponse, status_code=201)
async def create_new_provider(
    provider_data: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Create a new provider. Admin only."""
    provider = await create_provider(db, provider_data)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A provider with this email already exists",
        )
    return provider


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single provider by ID."""
    provider = await get_provider_by_id(db, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
    return provider


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_existing_provider(
    provider_id: uuid.UUID,
    provider_data: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    """Update a provider. Admin only."""
    provider = await update_provider(db, provider_id, provider_data)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
    return provider


@router.get("/{provider_id}/schedule", response_model=list)
async def get_provider_schedule(
    provider_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get upcoming appointments for a provider."""
    provider = await get_provider_by_id(db, provider_id)
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found",
        )
    return []  # Will be populated when appointments are built