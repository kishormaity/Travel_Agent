import json
import os
import pytest
from unittest.mock import MagicMock, patch

from app.schemas.flight import NormalizedFlightOffer, FlightSegment, FlightLayover
from app.agents.flight.agent import FlightAgent
from app.agents.flight.normalizer import (
    extract_raw_json,
    normalize_octotrip_flight,
    rank_flight_offers,
)


# =====================================================================
# Mock OctoTrip Payloads
# =====================================================================
MOCK_OCTOTRIP_ONEWAY_RAW = {
    "results": [
        {
            "airline": "British Airways",
            "airline_code": "BA",
            "flight_numbers": ["BA256"],
            "is_direct": True,
            "stops": 0,
            "price": 325.99,
            "currency": "EUR",
            "baggage": "No checked bag, Cabin bag: 6 piece(s)",
            "booking_url": "https://mcp.octotrip.app/flights/r/01a19655?u=19200068",
            "gate": "Wingie",
            "tags": ["convenient_ticket", "direct"],
            "outbound": {
                "departure": "DEL",
                "arrival": "LHR",
                "departure_date": "2026-12-15",
                "arrival_date": "2026-12-15",
                "departure_time": "10:50",
                "arrival_time": "15:15",
                "duration_minutes": 595,
                "legs": [
                    {
                        "carrier": "British Airways",
                        "flight_number": "BA256",
                        "aircraft": "Airbus A350-1000",
                        "departure": "DEL",
                        "arrival": "LHR",
                        "departure_time": "10:50",
                        "arrival_time": "15:15",
                        "departure_date": "2026-12-15",
                        "arrival_date": "2026-12-15",
                        "duration_minutes": 595,
                    }
                ],
            },
        },
        {
            "airline": "Etihad Airways",
            "airline_code": "EY",
            "flight_numbers": ["EY215", "EY63"],
            "is_direct": False,
            "stops": 1,
            "price": 249.62,
            "currency": "EUR",
            "baggage": "No checked bag, Cabin bag: 3x7kg",
            "booking_url": "https://mcp.octotrip.app/flights/r/01a19655?u=11200008",
            "gate": "Flightnetwork",
            "tags": ["convenient_ticket", "has_transfer"],
            "outbound": {
                "departure": "DEL",
                "arrival": "LHR",
                "departure_date": "2026-12-15",
                "arrival_date": "2026-12-16",
                "departure_time": "16:20",
                "arrival_time": "12:05",
                "duration_minutes": 1515,
                "legs": [
                    {
                        "carrier": "Etihad Airways",
                        "flight_number": "EY215",
                        "aircraft": "Airbus A321neo",
                        "departure": "DEL",
                        "arrival": "AUH",
                        "departure_time": "16:20",
                        "arrival_time": "18:50",
                        "departure_date": "2026-12-15",
                        "arrival_date": "2026-12-15",
                        "duration_minutes": 240,
                    },
                    {
                        "carrier": "Etihad Airways",
                        "flight_number": "EY63",
                        "aircraft": "Boeing 787-9",
                        "departure": "AUH",
                        "arrival": "LHR",
                        "departure_time": "08:10",
                        "arrival_time": "12:05",
                        "departure_date": "2026-12-16",
                        "arrival_date": "2026-12-16",
                        "duration_minutes": 445,
                    },
                ],
            },
        },
        {
            "airline": "Air India",
            "airline_code": "AI",
            "flight_numbers": ["AI111"],
            "is_direct": True,
            "stops": 0,
            "price": 391.27,
            "currency": "EUR",
            "baggage": "Checked bag: 1x23kg, Cabin bag: 5x7kg",
            "booking_url": "https://mcp.octotrip.app/flights/r/01a19655?u=19200118",
            "gate": "Wingie",
            "tags": ["direct", "convenient_ticket"],
            "outbound": {
                "departure": "DEL",
                "arrival": "LHR",
                "departure_date": "2026-12-15",
                "arrival_date": "2026-12-15",
                "departure_time": "05:00",
                "arrival_time": "11:30",
                "duration_minutes": 720,
                "legs": [
                    {
                        "carrier": "Air India",
                        "flight_number": "AI111",
                        "aircraft": "Boeing 787-9",
                        "departure": "DEL",
                        "arrival": "LHR",
                        "departure_time": "05:00",
                        "arrival_time": "11:30",
                        "departure_date": "2026-12-15",
                        "arrival_date": "2026-12-15",
                        "duration_minutes": 720,
                    }
                ],
            },
        },
    ],
    "total_available": 1473,
}

MOCK_OCTOTRIP_ROUNDTRIP_RAW = {
    "results": [
        {
            "airline": "British Airways",
            "airline_code": "BA",
            "flight_numbers": ["BA256", "BA257"],
            "is_direct": True,
            "stops": 0,
            "price": 650.00,
            "currency": "EUR",
            "baggage": "Checked bag: 1x23kg",
            "booking_url": "https://mcp.octotrip.app/flights/r/rt123",
            "gate": "Wingie",
            "outbound": {
                "departure": "DEL",
                "arrival": "LHR",
                "departure_date": "2026-12-15",
                "arrival_date": "2026-12-15",
                "departure_time": "10:50",
                "arrival_time": "15:15",
                "duration_minutes": 595,
                "legs": [
                    {
                        "carrier": "British Airways",
                        "flight_number": "BA256",
                        "aircraft": "Airbus A350-1000",
                        "departure": "DEL",
                        "arrival": "LHR",
                        "departure_time": "10:50",
                        "arrival_time": "15:15",
                    }
                ],
            },
            "inbound": {
                "departure": "LHR",
                "arrival": "DEL",
                "departure_date": "2026-12-22",
                "arrival_date": "2026-12-23",
                "departure_time": "18:00",
                "arrival_time": "08:30",
                "duration_minutes": 540,
                "legs": [
                    {
                        "carrier": "British Airways",
                        "flight_number": "BA257",
                        "aircraft": "Airbus A350-1000",
                        "departure": "LHR",
                        "arrival": "DEL",
                        "departure_time": "18:00",
                        "arrival_time": "08:30",
                    }
                ],
            },
        }
    ]
}


# =====================================================================
# 1. Test Tool Discovery
# =====================================================================
def test_octotrip_tool_discovery():
    """Verify that OctoTrip search tool is discovered and identified properly."""
    tools_cache = {
        "flight_octotrip_search": MagicMock(description="OctoTrip live flight search"),
    }
    tool = next((name for name in tools_cache if "octotrip" in name.lower()), None)
    assert tool == "flight_octotrip_search"


# =====================================================================
# 2. Test One-Way Flight Search
# =====================================================================
def test_oneway_flight_search():
    """Verify one-way flight search invokes OctoTrip with correct arguments and parses results."""
    agent = FlightAgent()
    mock_res = {
        "success": True,
        "data": [{"type": "text", "text": json.dumps(MOCK_OCTOTRIP_ONEWAY_RAW)}],
    }

    with patch("app.mcp.remote.remote_mcp_manager.ensure_initialized"), \
         patch("app.mcp.remote.remote_mcp_manager._tools_cache", {"flight_octotrip_search": MagicMock()}), \
         patch("app.mcp.remote.remote_mcp_manager.execute_tool", return_value=mock_res) as mock_exec:

        out = agent.execute(departure_iata="DEL", arrival_iata="LHR", flight_date="2026-12-15")

        assert out.success is True
        assert out.data["count"] == 3
        assert len(out.flights) == 3
        assert mock_exec.call_args[1]["arguments"]["origin"] == "DEL"
        assert mock_exec.call_args[1]["arguments"]["destination"] == "LHR"
        assert mock_exec.call_args[1]["arguments"]["departure_date"] == "2026-12-15"
        assert "return_date" not in mock_exec.call_args[1]["arguments"]


# =====================================================================
# 3. Test Round-Trip Flight Search
# =====================================================================
def test_roundtrip_flight_search():
    """Verify round-trip search passes return_date and parses both outbound and inbound segments."""
    agent = FlightAgent()
    mock_res = {
        "success": True,
        "data": [{"type": "text", "text": json.dumps(MOCK_OCTOTRIP_ROUNDTRIP_RAW)}],
    }

    with patch("app.mcp.remote.remote_mcp_manager.ensure_initialized"), \
         patch("app.mcp.remote.remote_mcp_manager._tools_cache", {"flight_octotrip_search": MagicMock()}), \
         patch("app.mcp.remote.remote_mcp_manager.execute_tool", return_value=mock_res) as mock_exec:

        out = agent.execute(
            departure_iata="DEL",
            arrival_iata="LHR",
            flight_date="2026-12-15",
            return_date="2026-12-22",
        )

        assert out.success is True
        assert mock_exec.call_args[1]["arguments"]["return_date"] == "2026-12-22"
        offer = out.flights[0]
        assert offer["is_round_trip"] is True
        assert len(offer["segments"]) == 1
        assert len(offer["inbound_segments"]) == 1
        assert offer["inbound_segments"][0]["origin"] == "LHR"
        assert offer["inbound_segments"][0]["destination"] == "DEL"


# =====================================================================
# 4. Test Direct Flight Normalization
# =====================================================================
def test_direct_flight_normalization():
    """Verify that direct flights are flagged with is_direct=True, stops=0, and 1 segment."""
    offer = normalize_octotrip_flight(MOCK_OCTOTRIP_ONEWAY_RAW["results"][0], "DEL", "LHR")
    assert offer.is_direct is True
    assert offer.stops == 0
    assert len(offer.segments) == 1
    assert offer.segments[0].flight_number == "BA256"
    assert offer.segments[0].aircraft == "Airbus A350-1000"


# =====================================================================
# 5. Test Connecting Flight Segments and Layovers
# =====================================================================
def test_connecting_flight_segments_and_layovers():
    """Verify that connecting flights retain individual legs, aircraft, and connection layovers."""
    offer = normalize_octotrip_flight(MOCK_OCTOTRIP_ONEWAY_RAW["results"][1], "DEL", "LHR")
    assert offer.is_direct is False
    assert offer.stops == 1
    assert len(offer.segments) == 2
    assert offer.segments[0].flight_number == "EY215"
    assert offer.segments[0].destination == "AUH"
    assert offer.segments[1].flight_number == "EY63"
    assert offer.segments[1].origin == "AUH"
    assert len(offer.layovers) == 1
    assert offer.layovers[0].airport == "AUH"


# =====================================================================
# 6. Test Price, Currency, and Booking Link Preservation
# =====================================================================
def test_price_currency_and_booking_link_preservation():
    """Verify that price, currency, gate, and booking URLs are preserved without fabrication."""
    offer = normalize_octotrip_flight(MOCK_OCTOTRIP_ONEWAY_RAW["results"][0], "DEL", "LHR")
    assert offer.price == 325.99
    assert offer.currency == "EUR"
    assert offer.is_bookable is True
    assert "https://mcp.octotrip.app/flights/r/" in offer.booking_url
    assert offer.raw_metadata["gate"] == "Wingie"


# =====================================================================
# 7. Test Baggage and Fare Preservation
# =====================================================================
def test_baggage_and_fare_preservation():
    """Verify that baggage information returned by OctoTrip is preserved in the offer."""
    offer = normalize_octotrip_flight(MOCK_OCTOTRIP_ONEWAY_RAW["results"][2], "DEL", "LHR")
    assert "Checked bag: 1x23kg" in offer.baggage
    assert "Cabin bag: 5x7kg" in offer.baggage


# =====================================================================
# 8. Test Flight Ranking Dimensions
# =====================================================================
def test_flight_ranking_dimensions():
    """Verify that ranking correctly sorts by cheapest, fastest, fewest stops, and best overall value."""
    offers = [normalize_octotrip_flight(f, "DEL", "LHR") for f in MOCK_OCTOTRIP_ONEWAY_RAW["results"]]
    ranked = rank_flight_offers(offers)

    # Cheapest should be Etihad at 249.62
    cheapest = ranked["cheapest"]
    assert cheapest[0].airline == "Etihad Airways"
    assert cheapest[0].price == 249.62

    # Fastest should be British Airways at 595 min
    fastest = ranked["fastest"]
    assert fastest[0].airline == "British Airways"
    assert fastest[0].total_duration_minutes == 595

    # Fewest stops should prioritize direct flights (stops=0)
    fewest_stops = ranked["fewest_stops"]
    assert fewest_stops[0].stops == 0
    assert fewest_stops[1].stops == 0
    assert fewest_stops[2].stops == 1

    # Best value combines price and duration
    best_value = ranked["best_value"]
    assert len(best_value) == 3
    for f in best_value:
        assert f.best_value_score is not None
        assert "best_value_rank" in f.rankings


# =====================================================================
# 9. Test Error Handling and Timeouts
# =====================================================================
def test_error_handling_and_timeouts():
    """Verify that OctoTrip network errors return success=False with clear error details."""
    FlightAgent.clear_cache()
    agent = FlightAgent()

    with patch("app.mcp.remote.remote_mcp_manager.ensure_initialized"), \
         patch("app.mcp.remote.remote_mcp_manager._tools_cache", {"flight_octotrip_search": MagicMock()}), \
         patch("app.mcp.remote.remote_mcp_manager.execute_tool", return_value={"success": False, "error": "Remote MCP HTTP 504 Gateway Timeout"}):

        out = agent.execute(departure_iata="DEL", arrival_iata="LHR", flight_date="2026-12-15")
        assert out.success is False
        assert "Gateway Timeout" in out.error
        assert out.flights == []


# =====================================================================
# 10. Test Empty Results Handling
# =====================================================================
def test_empty_results_handling():
    """Verify that when OctoTrip returns 0 results, the agent reports success=True with empty flights."""
    FlightAgent.clear_cache()
    agent = FlightAgent()
    empty_res = {
        "success": True,
        "data": [{"type": "text", "text": json.dumps({"results": []})}],
    }

    with patch("app.mcp.remote.remote_mcp_manager.ensure_initialized"), \
         patch("app.mcp.remote.remote_mcp_manager._tools_cache", {"flight_octotrip_search": MagicMock()}), \
         patch("app.mcp.remote.remote_mcp_manager.execute_tool", return_value=empty_res):

        out = agent.execute(departure_iata="DEL", arrival_iata="LHR", flight_date="2026-12-15")
        assert out.success is True
        assert out.data["count"] == 0
        assert out.flights == []
        assert "No commercial flights available" in out.summary


# =====================================================================
# 11. Opt-In Live OctoTrip Integration Test
# =====================================================================
@pytest.mark.skipif(
    not os.getenv("RUN_LIVE_OCTOTRIP_TEST"),
    reason="Live integration test skipped by default. Set RUN_LIVE_OCTOTRIP_TEST=1 to execute.",
)
def test_live_octotrip_integration():
    """Opt-in live integration test against the real OctoTrip MCP endpoint."""
    agent = FlightAgent()
    out = agent.execute(
        departure_iata="DEL",
        arrival_iata="LHR",
        flight_date="2026-12-15",
        currency="EUR",
    )
    assert out.success is True
    assert out.data["count"] > 0
    assert len(out.flights) > 0
    assert out.data["provider"] == "flight_octotrip"
