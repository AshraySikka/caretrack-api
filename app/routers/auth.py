from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.users import UserCreate, UserLogin, UserResponse, TokenResponse, UserUpdate
from app.services.auth_service import register_user, login_user, get_user_by_email
from app.dependencies import get_current_user
from app.models.users import User

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    user = await register_user(db, user_data)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists",
        )
    return user


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and receive a JWT access token."""
    result = await login_user(db, user_data.email, user_data.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the currently logged in user's profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the currently logged in user's profile."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.email is not None:
        existing = await get_user_by_email(db, user_update.email)
        if existing and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already in use",
            )
        current_user.email = user_update.email
    await db.flush()
    await db.refresh(current_user)
    return current_user