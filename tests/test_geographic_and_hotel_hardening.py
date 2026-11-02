import pytest
from app.services.geocoding_service import GeocodingService
from app.services.maps_service import MapsService, haversine_distance_km
from app.services.places_service import PlacesService
from app.tools.hotels import search_hotels
from app.tools.weather import get_current_weather


@pytest.fixture
def geocoding_service():
    return GeocodingService()


@pytest.fixture
def maps_service():
    return MapsService()


@pytest.fixture
def places_service():
    return PlacesService()


def test_geocoding_distinguishes_kochi_india_from_japan(geocoding_service):
    """Test case: Kochi, India must resolve to Kerala, while Kochi, Japan resolves to Japan."""
    # 1. Bare 'Kochi' (domestic default)
    kochi_india = geocoding_service.get_coordinates("Kochi")
    assert kochi_india["country_code"] == "in"
    assert kochi_india["state"] == "Kerala"
    assert abs(kochi_india["latitude"] - 9.967) < 0.2
    assert abs(kochi_india["longitude"] - 76.244) < 0.2

    # 2. Explicit 'Kochi, Kerala, India'
    kochi_explicit = geocoding_service.get_coordinates("Kochi, Kerala, India")
    assert kochi_explicit["country_code"] == "in"
    assert kochi_explicit["state"] == "Kerala"

    # 3. Explicit 'Kochi, Japan'
    kochi_japan = geocoding_service.get_coordinates("Kochi, Japan")
    assert kochi_japan["country_code"] == "jp"
    assert abs(kochi_japan["latitude"] - 33.5) < 1.0
    assert abs(kochi_japan["longitude"] - 133.5) < 1.0


def test_geocoding_kerala_destinations_and_international(geocoding_service):
    """Test cases: Munnar, Alleppey, London, UK, Delhi, India."""
    # Munnar
    munnar = geocoding_service.get_coordinates("Munnar, Kerala, India")
    assert munnar["country_code"] == "in"
    assert abs(munnar["latitude"] - 10.08) < 0.2

    # Alleppey
    alleppey = geocoding_service.get_coordinates("Alleppey, Kerala, India")
    assert alleppey["country_code"] == "in"
    assert abs(alleppey["latitude"] - 9.49) < 0.2

    # Delhi
    delhi = geocoding_service.get_coordinates("Delhi, India")
    assert delhi["country_code"] == "in"
    assert abs(delhi["latitude"] - 28.61) < 0.2

    # London, UK
    london = geocoding_service.get_coordinates("London, UK")
    assert london["country_code"] == "gb"
    assert abs(london["latitude"] - 51.5) < 0.5


def test_maps_driving_routes_plausibility(maps_service):
    """Verify route distances are geographically plausible for Kerala travel."""
    # Kochi to Munnar: ~130 km
    r1 = maps_service.get_route("Kochi", "Munnar")
    assert r1["status"] == "success"
    assert 100 < r1["distance_km"] < 180, f"Distance {r1.get('distance_km')} km out of range"
    assert 60 < r1["duration_minutes"] < 240

    # Munnar to Alleppey: ~155-180 km
    r2 = maps_service.get_route("Munnar", "Alleppey")
    assert r2["status"] == "success"
    assert 130 < r2["distance_km"] < 210, f"Distance {r2.get('distance_km')} km out of range"


def test_maps_rejects_geographically_impossible_route(maps_service):
    """Verify system rejects impossible routes crossing oceans instead of fabricating distances."""
    res = maps_service.get_route("Kochi", "London, UK")
    assert res["status"] == "no_route_found"
    assert "geographically impossible" in res["message"].lower() or "not possible" in res["message"].lower()


def test_places_search_kochi_returns_kerala_sights(places_service):
    """Verify searching places in Kochi returns Kerala attractions, zero Japanese locations."""
    places = places_service.search_places("Kochi", category="tourism.attraction", limit=5)
    assert len(places) > 0
    for place in places:
        addr = place["address"].lower()
        assert "japan" not in addr
        assert "kochi prefecture" not in addr


def test_hotel_search_transparency_and_room_guidance():
    """Verify hotel search returns rich metadata without fabricating live prices or assuming 3 rooms for 3 adults."""
    res = search_hotels.invoke({
        "city": "Kochi",
        "check_in_date": "2027-01-10",
        "check_out_date": "2027-01-12",
        "adults": 3,
        "limit": 3
    })
    assert res.success is True
    hotels = res.data
    assert len(hotels) > 0
    first = hotels[0]
    assert isinstance(first["live_rates_available"], bool)
    assert first["recommended_rooms"] in {1, 2}
    assert "Do not assume 3 separate rooms are needed" in first["room_guidance"]
    assert first["check_in_date"] == "2027-01-10"


def test_weather_observation_metadata_integrity():
    """Verify weather tool returns observation metadata distinguishing from future forecasts."""
    res = get_current_weather.invoke({"city": "Kochi"})
    assert res.success is True
    w = res.data
    assert w["data_type"] == "realtime_observation"
    assert "WeatherAPI" in w["provider"]
    assert "Not a forecast for future travel" in w["forecast_notice"]
    assert w["historical_climate_data_available"] is False
