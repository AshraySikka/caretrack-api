import pytest


@pytest.mark.asyncio
async def test_create_patient(client, auth_headers):
    """Test successful patient creation."""
    response = await client.post("/api/v1/patients/", headers=auth_headers, json={
        "first_name": "John",
        "last_name": "Smith",
        "date_of_birth": "1965-03-15",
        "health_card_no": "OHIP-TEST-001",
        "phone": "416-555-0101",
        "email": "john.smith@email.com",
        "address": "123 Main St, Toronto, ON"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Smith"
    assert data["health_card_no"] == "OHIP-TEST-001"
    assert data["status"] == "active"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_patient_duplicate_health_card(client, auth_headers):
    """Test that duplicate health card number is rejected."""
    await client.post("/api/v1/patients/", headers=auth_headers, json={
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1970-05-20",
        "health_card_no": "OHIP-TEST-002",
    })
    response = await client.post("/api/v1/patients/", headers=auth_headers, json={
        "first_name": "Another",
        "last_name": "Person",
        "date_of_birth": "1980-01-01",
        "health_card_no": "OHIP-TEST-002",
    })
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_patients(client, auth_headers):
    """Test listing patients returns paginated response."""
    await client.post("/api/v1/patients/", headers=auth_headers, json={
        "first_name": "List",
        "last_name": "Test",
        "date_of_birth": "1975-08-10",
        "health_card_no": "OHIP-TEST-003",
    })
    response = await client.get("/api/v1/patients/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "patients" in data
    assert isinstance(data["patients"], list)


@pytest.mark.asyncio
async def test_get_patient_by_id(client, auth_headers):
    """Test getting a single patient by ID."""
    create_response = await client.post(
        "/api/v1/patients/", headers=auth_headers, json={
            "first_name": "Single",
            "last_name": "Patient",
            "date_of_birth": "1980-12-01",
            "health_card_no": "OHIP-TEST-004",
        }
    )
    patient_id = create_response.json()["id"]
    response = await client.get(
        f"/api/v1/patients/{patient_id}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["id"] == patient_id


@pytest.mark.asyncio
async def test_get_patient_not_found(client, auth_headers):
    """Test that requesting a non-existent patient returns 404."""
    response = await client.get(
        "/api/v1/patients/00000000-0000-0000-0000-000000000000",
        headers=auth_headers
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_patient(client, auth_headers):
    """Test updating a patient record."""
    create_response = await client.post(
        "/api/v1/patients/", headers=auth_headers, json={
            "first_name": "Update",
            "last_name": "Me",
            "date_of_birth": "1990-06-15",
            "health_card_no": "OHIP-TEST-005",
        }
    )
    patient_id = create_response.json()["id"]
    response = await client.put(
        f"/api/v1/patients/{patient_id}",
        headers=auth_headers,
        json={"phone": "416-999-0000"}
    )
    assert response.status_code == 200
    assert response.json()["phone"] == "416-999-0000"


@pytest.mark.asyncio
async def test_list_patients_requires_auth(client):
    """Test that listing patients without auth returns 401."""
    response = await client.get("/api/v1/patients/")
    assert response.status_code == 401