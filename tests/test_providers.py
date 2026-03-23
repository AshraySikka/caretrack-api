import pytest


@pytest.mark.asyncio
async def test_create_provider_as_admin(client, admin_headers):
    """Test that admin can create a provider."""
    response = await client.post("/api/v1/providers/", headers=admin_headers, json={
        "first_name": "Sarah",
        "last_name": "Johnson",
        "provider_type": "RN",
        "license_number": "RN-TEST-001",
        "phone": "416-555-0202",
        "email": "sarah.test@caretrack.com",
        "max_patients": 25
    })
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "Sarah"
    assert data["provider_type"] == "RN"
    assert data["is_available"] is True


@pytest.mark.asyncio
async def test_create_provider_as_coordinator(client, auth_headers):
    """Test that coordinator cannot create a provider."""
    response = await client.post("/api/v1/providers/", headers=auth_headers, json={
        "first_name": "Bob",
        "last_name": "Smith",
        "provider_type": "PSW",
    })
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_providers(client, auth_headers):
    """Test listing providers returns paginated response."""
    response = await client.get("/api/v1/providers/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "providers" in data


@pytest.mark.asyncio
async def test_list_providers_filter_by_type(client, admin_headers, auth_headers):
    """Test filtering providers by type."""
    await client.post("/api/v1/providers/", headers=admin_headers, json={
        "first_name": "Filter",
        "last_name": "Test",
        "provider_type": "PT",
        "email": "filter.test@caretrack.com",
    })
    response = await client.get(
        "/api/v1/providers/?provider_type=PT",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    for provider in data["providers"]:
        assert provider["provider_type"] == "PT"


@pytest.mark.asyncio
async def test_get_provider_not_found(client, auth_headers):
    """Test that requesting a non-existent provider returns 404."""
    response = await client.get(
        "/api/v1/providers/00000000-0000-0000-0000-000000000000",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_providers_requires_auth(client):
    """Test that listing providers without auth returns 401."""
    response = await client.get("/api/v1/providers/")
    assert response.status_code == 401