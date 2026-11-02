import pytest
from unittest.mock import MagicMock, patch
from app.core.config import settings
from app.tools.hotels import search_hotels
from app.agents.accommodation.normalizer import (
    extract_raw_json,
    normalize_hasdata_property,
    normalize_hasdata_hotel_results,
)


def test_hasdata_api_key_loading():
    """Verify that settings correctly loads the HasData API key without exposure."""
    assert hasattr(settings, "hasdata_api_key")
    # Must not be None if configured in .env
    assert settings.hasdata_mcp_url == "https://mcp.hasdata.com/mcp"


def test_normalize_hasdata_property_with_pricing():
    """Verify property normalization with live Google Hotels rates and ratings."""
    prop = {
        "name": "Grand Hyatt Kochi Bolgatty",
        "hotelClass": "5-star hotel",
        "overallRating": 4.7,
        "reviews": 19364,
        "ratePerNight": {
            "lowest": "₹33,040",
            "extractedLowest": 33040,
            "beforeTaxesFees": "₹28,000",
        },
        "totalRate": {
            "lowest": "₹66,080",
            "extractedLowest": 66080,
            "beforeTaxesFees": "₹56,000",
        },
        "gpsCoordinates": {"latitude": 9.987342, "longitude": 76.264687},
        "link": "https://www.hyatt.com/grand-hyatt",
        "description": "Luxury waterfront resort",
    }

    norm = normalize_hasdata_property(
        prop,
        city="Kochi",
        check_in_date="2027-01-10",
        check_out_date="2027-01-12",
        adults=3,
    )

    assert norm["name"] == "Grand Hyatt Kochi Bolgatty"
    assert norm["hotel_class"] == "5-star hotel"
    assert norm["rating"] == 4.7
    assert norm["reviews"] == 19364
    assert norm["price_per_night"] == 33040
    assert norm["price_per_night_formatted"] == "₹33,040"
    assert norm["total_price"] == 66080
    assert norm["total_price_formatted"] == "₹66,080"
    assert norm["live_rates_available"] is True
    assert norm["data_source"] == "HasData (Google Hotels)"
    assert norm["recommended_rooms"] == 2
    assert "2 room(s) is typical" in norm["room_guidance"]
    assert norm["booking_url"] == "https://www.hyatt.com/grand-hyatt"


def test_normalize_hasdata_property_missing_pricing():
    """Verify graceful handling when pricing is unavailable for specific dates."""
    prop = {
        "name": "Taj Malabar Resort & Spa",
        "hotelClass": "5-star hotel",
        "overallRating": 4.6,
        "reviews": 6493,
        "ratePerNight": None,
        "totalRate": None,
        "gpsCoordinates": {"latitude": 9.9688, "longitude": 76.2582},
        "link": "https://www.tajhotels.com",
    }

    norm = normalize_hasdata_property(
        prop,
        city="Kochi",
        check_in_date="2027-01-10",
        check_out_date="2027-01-12",
        adults=2,
    )

    assert norm["name"] == "Taj Malabar Resort & Spa"
    assert norm["live_rates_available"] is False
    assert norm["price_per_night"] is None
    assert norm["total_price"] is None
    assert "verify directly on booking sites" in norm["pricing_notice"]
    assert norm["recommended_rooms"] == 1


def test_normalize_hasdata_hotel_results_deduplication():
    """Verify duplicate hotel properties with identical names are cleanly removed."""
    raw_payload = [
        {
            "text": """{
                "status": 200,
                "json": {
                    "properties": [
                        {"name": "Tea County Munnar", "hotelClass": "4-star", "overallRating": 4.5},
                        {"name": "tea county munnar", "hotelClass": "4-star", "overallRating": 4.5},
                        {"name": "Grand Plaza Munnar", "hotelClass": "4-star", "overallRating": 4.6}
                    ]
                }
            }"""
        }
    ]

    results = normalize_hasdata_hotel_results(
        raw_response=raw_payload,
        city="Munnar",
        limit=5,
    )

    assert len(results) == 2
    names = [r["name"] for r in results]
    assert names == ["Tea County Munnar", "Grand Plaza Munnar"]


def test_search_hotels_hasdata_primary_success():
    """Verify search_hotels successfully calls HasData when configured and returns normalized data."""
    mock_data = [
        {
            "text": """{
                "status": 200,
                "json": {
                    "properties": [
                        {"name": "Grand Hyatt Kochi", "hotelClass": "5-star", "overallRating": 4.7, "ratePerNight": {"extractedLowest": 33040}}
                    ]
                }
            }"""
        }
    ]

    with patch("app.tools.hotels.settings.hasdata_api_key", "test_key_123"), \
         patch("app.tools.hotels.remote_mcp_manager.execute_tool") as mock_exec:
        mock_exec.return_value = {"success": True, "data": mock_data}

        res = search_hotels.invoke({
            "city": "Kochi",
            "check_in_date": "2027-01-10",
            "check_out_date": "2027-01-12",
            "adults": 3,
        })

        assert res.success is True
        assert len(res.data) == 1
        assert res.data[0]["name"] == "Grand Hyatt Kochi"
        assert res.data[0]["live_rates_available"] is True
        assert res.data[0]["data_source"] == "HasData (Google Hotels)"


def test_search_hotels_fallback_on_401_or_failure():
    """Verify that if HasData returns an error (such as 401 or timeout), it falls back seamlessly to Geoapify."""
    fallback_places = [
        {
            "name": "Nila",
            "address": "Edapally, Kochi",
            "data_source": "geoapify_places",
            "live_rates_available": False,
        }
    ]

    with patch("app.tools.hotels.settings.hasdata_api_key", "invalid_key"), \
         patch("app.tools.hotels.remote_mcp_manager.execute_tool") as mock_exec, \
         patch("app.tools.hotels._places_service.search_places") as mock_geo:
        # Simulate HasData 401 Unauthorized failure
        mock_exec.return_value = {"success": False, "error": "HTTPStatusError: 401 Unauthorized"}
        mock_geo.return_value = fallback_places

        res = search_hotels.invoke({
            "city": "Kochi",
            "check_in_date": "2027-01-10",
            "check_out_date": "2027-01-12",
            "adults": 3,
        })

        assert res.success is True
        assert len(res.data) == 1
        assert res.data[0]["name"] == "Nila"
        assert res.data[0]["data_source"] == "geoapify_places"
        mock_geo.assert_called_once()


def test_search_hotels_fallback_on_exception():
    """Verify that if HasData raises an unexpected exception/timeout, it catches it and falls back to Geoapify."""
    fallback_places = [{"name": "Fallback Hotel", "data_source": "geoapify_places"}]

    with patch("app.tools.hotels.settings.hasdata_api_key", "test_key"), \
         patch("app.tools.hotels.remote_mcp_manager.execute_tool", side_effect=TimeoutError("HasData timed out")), \
         patch("app.tools.hotels._places_service.search_places", return_value=fallback_places) as mock_geo:

        res = search_hotels.invoke({
            "city": "Munnar",
            "check_in_date": "2027-01-12",
            "check_out_date": "2027-01-14",
            "adults": 2,
        })

        assert res.success is True
        assert res.data[0]["name"] == "Fallback Hotel"
        mock_geo.assert_called_once()
