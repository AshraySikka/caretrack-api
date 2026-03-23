import pytest


@pytest.mark.asyncio
async def test_register_user(client):
    """Test successful user registration."""
    response = await client.post("/api/v1/auth/register", json={
        "email": "newuser@caretrack.com",
        "full_name": "New User",
        "password": "password123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@caretrack.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "coordinator"
    assert "hashed_password" not in data
    assert "password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Test that registering with an existing email fails."""
    await client.post("/api/v1/auth/register", json={
        "email": "duplicate@caretrack.com",
        "full_name": "First User",
        "password": "password123"
    })
    response = await client.post("/api/v1/auth/register", json={
        "email": "duplicate@caretrack.com",
        "full_name": "Second User",
        "password": "password456"
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client):
    """Test successful login returns JWT token."""
    await client.post("/api/v1/auth/register", json={
        "email": "login@caretrack.com",
        "full_name": "Login User",
        "password": "password123"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "login@caretrack.com",
        "password": "password123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Test that wrong password returns 401."""
    await client.post("/api/v1/auth/register", json={
        "email": "wrongpass@caretrack.com",
        "full_name": "Wrong Pass User",
        "password": "correctpassword"
    })
    response = await client.post("/api/v1/auth/login", json={
        "email": "wrongpass@caretrack.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_email(client):
    """Test that login with unknown email returns 401."""
    response = await client.post("/api/v1/auth/login", json={
        "email": "nobody@caretrack.com",
        "password": "password123"
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client, auth_headers):
    """Test getting current user profile."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@caretrack.com"
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_get_me_no_token(client):
    """Test that protected route rejects requests without token."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client):
    """Test that invalid token returns 401."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401