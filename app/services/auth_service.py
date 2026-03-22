from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.users import User
from app.schemas.users import UserCreate
from app.utils.security import hash_password, verify_password, create_access_token
from app.config import settings


async def get_user_by_email(db: AsyncSession, email: str):
    """Fetch a single user from the database by their email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def register_user(db: AsyncSession, user_data: UserCreate):
    """
    Register a new user.
    1. Check if email is already taken
    2. Hash the password
    3. Save the new user to the database
    """
    # Check if a user with this email already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        return None  # Signal to the router that registration failed

    # Hash the password before storing
    hashed = hash_password(user_data.password)

    # Create the new User object
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed,
    )

    # Add to database and save
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    return new_user


async def login_user(db: AsyncSession, email: str, password: str):
    """
    Log in a user.
    1. Find the user by email
    2. Verify the password
    3. Return a JWT token
    """
    # Find the user
    user = await get_user_by_email(db, email)

    # If user not found or password is wrong, return None
    if not user or not verify_password(password, user.hashed_password):
        return None

    # If user is disabled
    if not user.is_active:
        return None

    # Create and return a JWT token
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}