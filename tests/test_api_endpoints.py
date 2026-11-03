import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def api_client():
    return TestClient(app)


def test_health_endpoints(api_client):
    """Verify health and ready probes respond successfully."""
    res = api_client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    res_v1 = api_client.get("/api/v1/health")
    assert res_v1.status_code == 200
    assert res_v1.json()["status"] == "healthy"


def test_get_trip_default(api_client):
    """Verify GET /api/v1/trips/{trip_id} returns structured trip data."""
    res = api_client.get("/api/v1/trips/trip-demo")
    assert res.status_code == 200
    data = res.json()
    assert "trip_id" in data
    assert "structured_data" in data
    assert data["destination"] == "Kochi, Munnar, Alleppey, Kerala"
    assert data["travelers"] == 3
    assert data["budget"] == 90000.0


def test_trip_extractor_function():
    """Verify extractor properly structures raw planner outcomes."""
    from app.services.trip_extractor import extract_structured_trip_data

    structured = extract_structured_trip_data(
        user_goal="Plan a 7-day Kerala trip for 3 adults from Delhi to Kochi, Munnar, Alleppey with budget ₹90,000",
        final_response="Trip Overview\nWonderful journey.\n\nFlight Details\nDEL to COK.",
        trip_id="test-123",
    )
    assert structured["trip_id"] == "test-123"
    assert "Kochi" in structured["destinations"]
    assert "Munnar" in structured["destinations"]
    assert "Alleppey" in structured["destinations"]
    assert structured["travelers"]["count"] == 3
    assert structured["budget"]["user_budget"] == 90000.0
    assert len(structured["itinerary"]) == 7

