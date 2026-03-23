import os
import asyncio
import pytest  # noqa
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.database import Base, get_db

# Build test database URL
_base_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:password@localhost:5432/caretrack"
)

if "/caretrack_test" in _base_url:
    TEST_DATABASE_URL = _base_url
else:
    TEST_DATABASE_URL = _base_url.replace("/caretrack", "/caretrack_test")

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    """Override the database dependency to use test database."""
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """Create all tables in test database before tests run."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database):
    """Give each test a clean database session."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(setup_database):
    """Give each test a fresh HTTP client with test database."""
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def auth_headers(client):
    """Register and login a test user, return auth headers."""
    await client.post("/api/v1/auth/register", json={
        "email": "test@caretrack.com",
        "full_name": "Test User",
        "password": "testpassword123"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "test@caretrack.com",
        "password": "testpassword123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def admin_headers(client):
    """Register and login an admin user, return auth headers."""
    await client.post("/api/v1/auth/register", json={
        "email": "admin@caretrack.com",
        "full_name": "Admin User",
        "password": "adminpassword123"
    })
    async with TestSessionLocal() as session:
        from sqlalchemy.future import select
        from app.models.users import User
        result = await session.execute(
            select(User).where(User.email == "admin@caretrack.com")
        )
        user = result.scalars().first()
        user.role = "admin"
        await session.commit()

    response = await client.post("/api/v1/auth/login", json={
        "email": "admin@caretrack.com",
        "password": "adminpassword123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}