import pytest


async def create_test_patient(client, auth_headers, health_card="OHIP-CP-001"):
    """Helper to create a patient for care plan tests."""
    response = await client.post("/api/v1/patients/", headers=auth_headers, json={
        "first_name": "Care",
        "last_name": "Plan Patient",
        "date_of_birth": "1970-01-01",
        "health_card_no": health_card,
    })
    return response.json()["id"]


async def create_test_provider(client, admin_headers, email="cp.provider@caretrack.com"):
    """Helper to create a provider for care plan tests."""
    response = await client.post("/api/v1/providers/", headers=admin_headers, json={
        "first_name": "Care",
        "last_name": "Provider",
        "provider_type": "RN",
        "email": email,
    })
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_care_plan(client, auth_headers, admin_headers):
    """Test successful care plan creation."""
    patient_id = await create_test_patient(client, auth_headers, "OHIP-CP-002")
    provider_id = await create_test_provider(client, admin_headers, "cp2@caretrack.com")

    response = await client.post("/api/v1/care-plans/", headers=auth_headers, json={
        "patient_id": patient_id,
        "provider_id": provider_id,
        "title": "Test Care Plan",
        "description": "Test description",
        "goals": "Test goals",
        "start_date": "2026-04-01",
        "end_date": "2026-07-01"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Care Plan"
    assert data["status"] == "draft"
    assert data["patient"] is not None
    assert data["provider"] is not None
    assert data["creator"] is not None


@pytest.mark.asyncio
async def test_care_plan_status_transition(client, auth_headers, admin_headers):
    """Test valid status transition from draft to active."""
    patient_id = await create_test_patient(client, auth_headers, "OHIP-CP-003")
    provider_id = await create_test_provider(client, admin_headers, "cp3@caretrack.com")

    create_response = await client.post(
        "/api/v1/care-plans/", headers=auth_headers, json={
            "patient_id": patient_id,
            "provider_id": provider_id,
            "title": "Transition Test Plan",
            "start_date": "2026-04-01",
        }
    )
    care_plan_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/care-plans/{care_plan_id}/status",
        headers=auth_headers,
        json={"status": "active"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "active"


@pytest.mark.asyncio
async def test_care_plan_invalid_status_transition(client, auth_headers, admin_headers):
    """Test that invalid status transition is rejected."""
    patient_id = await create_test_patient(client, auth_headers, "OHIP-CP-004")
    provider_id = await create_test_provider(client, admin_headers, "cp4@caretrack.com")

    create_response = await client.post(
        "/api/v1/care-plans/", headers=auth_headers, json={
            "patient_id": patient_id,
            "provider_id": provider_id,
            "title": "Invalid Transition Plan",
            "start_date": "2026-04-01",
        }
    )
    care_plan_id = create_response.json()["id"]

    # Try to go directly from draft to completed — should fail
    response = await client.patch(
        f"/api/v1/care-plans/{care_plan_id}/status",
        headers=auth_headers,
        json={"status": "completed"}
    )
    assert response.status_code == 400
    assert "Cannot transition" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_care_plans(client, auth_headers):
    """Test listing care plans returns paginated response."""
    response = await client.get("/api/v1/care-plans/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "care_plans" in data


@pytest.mark.asyncio
async def test_care_plan_not_found(client, auth_headers):
    """Test that requesting a non-existent care plan returns 404."""
    response = await client.get(
        "/api/v1/care-plans/00000000-0000-0000-0000-000000000000",
        headers=auth_headers
    )
    assert response.status_code == 404