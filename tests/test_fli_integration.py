import os
import time
import subprocess
import requests
import pytest
from datetime import date, timedelta
from unittest.mock import patch

from app.mcp.remote import remote_mcp_manager
from app.agents.flight.agent import FlightAgent


# ---------------------------------------------------------------------------
# Fixture: Ensure Fli MCP Server is running on port 8001
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def fli_server_port_8001():
    """Starts fli MCP server if not running, yields base URL, tears down after."""
    url = os.getenv("FLI_MCP_URL", "http://127.0.0.1:8001/mcp/")
    health_url = url.replace("/mcp/", "/health").replace("/mcp", "/health")

    # Check if already running
    try:
        r = requests.get(health_url, timeout=2)
        if r.status_code == 200:
            yield url
            return
    except Exception:
        pass

    # Start fli MCP server process
    proc = subprocess.Popen(
        ["uv", "run", "--no-sync", "python", "-m", "app.mcp.servers.fli_server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Wait for health endpoint
    started = False
    for _ in range(30):
        try:
            r = requests.get(health_url, timeout=1)
            if r.status_code == 200:
                started = True
                break
        except Exception:
            time.sleep(0.5)

    if not started:
        proc.terminate()
        pytest.fail(f"Could not start Fli MCP server on {health_url}")

    try:
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=5)


# ---------------------------------------------------------------------------
# 1 & 2. Verify Server Startup, Port 8001, and /health
# ---------------------------------------------------------------------------
def test_fli_server_startup_and_health(fli_server_port_8001):
    """Verify Fli server is live on port 8001 and /health responds with status ok."""
    health_url = fli_server_port_8001.replace("/mcp/", "/health").replace("/mcp", "/health")
    resp = requests.get(health_url, timeout=5)
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


# ---------------------------------------------------------------------------
# 3. Verify MCP Tool Discovery via RemoteMCPClientManager
# ---------------------------------------------------------------------------
def test_fli_mcp_tool_discovery(fli_server_port_8001):
    """Verify tool discovery across RemoteMCPClientManager discovers Fli tools."""
    remote_mcp_manager.ensure_initialized()
    tools = remote_mcp_manager.get_tools_for_agent("flight_agent")
    tool_names = [t.name for t in tools]

    assert any(name.startswith("fli_search_flights") or name == "search_flights" for name in tool_names), (
        f"fli_search_flights not discovered in flight_agent tools: {tool_names}"
    )
    assert any(name.startswith("fli_search_dates") or name == "search_dates" for name in tool_names), (
        f"fli_search_dates not discovered in flight_agent tools: {tool_names}"
    )

    health = remote_mcp_manager.check_health()
    assert "providers" in health and "fli" in health["providers"]
    assert health["providers"]["fli"]["status"] == "connected"


# ---------------------------------------------------------------------------
# 4. Live One-Way Flight Search via Fli
# ---------------------------------------------------------------------------
def test_fli_search_flights_oneway(fli_server_port_8001):
    """Execute live one-way flight search from CCU to BLR via Fli."""
    agent = FlightAgent()
    agent.clear_cache()

    dep_date = (date.today() + timedelta(days=17)).strftime("%Y-%m-%d")
    result = agent.execute(
        departure_iata="CCU",
        arrival_iata="BLR",
        flight_date=dep_date,
        return_date=None,
        adults=1,
        currency="INR",
        bypass_cache=True,
    )

    assert result.success is True, f"Flight search failed: {result.error}"
    assert result.data.get("provider") == "fli", f"Expected provider 'fli', got {result.data.get('provider')}"
    assert len(result.flights) > 0, "No flight offers returned from Fli"

    print(f"\n" + "=" * 95)
    print(f">> FULL FLI GOOGLE FLIGHTS RESULTS: CCU -> BLR ({dep_date})")
    print(f">> Total Flights Returned: {len(result.flights)} | Provider: {result.data.get('provider_display_name')}")
    print("=" * 95)
    print(f"{'#':<3} {'AIRLINE':<18} {'FLIGHT #':<12} {'DEP':<7} {'ARR':<7} {'STOPS':<10} {'DURATION':<10} {'PRICE (INR)':<14}")
    print("-" * 95)

    for idx, f in enumerate(result.flights, 1):
        airline = f.get("airline") or "Unknown"
        fn = f.get("flight_number") or ", ".join(f.get("flight_numbers", [])) or "N/A"
        dep = f.get("departure_time") or "N/A"
        arr = f.get("arrival_time") or "N/A"
        stops_count = f.get("stops", 0)
        stops_str = f"{stops_count} stop(s)" if stops_count > 0 else "Non-stop"
        dur = f.get("duration_formatted") or "N/A"
        price_val = f.get("price", 0.0)
        price_str = f"INR {price_val:,.2f}"

        print(f"{idx:<3} {airline:<18} {fn:<12} {dep:<7} {arr:<7} {stops_str:<10} {dur:<10} {price_str:<14}")
        print(f"    Booking Link: {f.get('booking_url')}")
        print("-" * 95)

    # Validate all returned flight offers for complete, verified fields
    for idx, f in enumerate(result.flights, 1):
        assert f["origin"] == "CCU", f"Offer {idx}: origin mismatch {f.get('origin')}"
        assert f["destination"] == "BLR", f"Offer {idx}: destination mismatch {f.get('destination')}"
        assert f["is_round_trip"] is False, f"Offer {idx}: expected one-way"
        assert f["price"] > 0, f"Offer {idx}: expected positive price, got {f.get('price')}"
        assert f["currency"] == "INR", f"Offer {idx}: expected INR currency"
        assert f["departure_time"], f"Offer {idx}: missing departure_time"
        assert f["arrival_time"], f"Offer {idx}: missing arrival_time"
        assert f["flight_number"], f"Offer {idx}: missing flight_number"
        assert f["booking_url"] and f["booking_url"].startswith("http"), f"Offer {idx}: invalid booking URL"

    first = result.flights[0]
    assert "Fli (Google Flights)" in result.summary


# ---------------------------------------------------------------------------
# 5. Round-Trip Search
# ---------------------------------------------------------------------------
def test_fli_search_flights_roundtrip(fli_server_port_8001):
    """Execute live round-trip flight search from CCU to BLR via Fli."""
    agent = FlightAgent()
    agent.clear_cache()

    dep_date = (date.today() + timedelta(days=17)).strftime("%Y-%m-%d")
    ret_date = (date.today() + timedelta(days=22)).strftime("%Y-%m-%d")

    result = agent.execute(
        departure_iata="CCU",
        arrival_iata="BLR",
        flight_date=dep_date,
        return_date=ret_date,
        adults=1,
        currency="INR",
        bypass_cache=True,
    )

    assert result.success is True, f"Round-trip search failed: {result.error}"
    assert result.data.get("provider") == "fli"
    assert len(result.flights) > 0

    first = result.flights[0]
    assert first["is_round_trip"] is True
    assert first["origin"] == "CCU"
    assert first["destination"] == "BLR"
    assert first["return_origin"] == "BLR"
    assert first["return_destination"] == "CCU"
    assert len(first.get("inbound_segments", [])) > 0
    assert first["price"] > 0


# ---------------------------------------------------------------------------
# 6. Test search_dates
# ---------------------------------------------------------------------------
def test_fli_search_dates(fli_server_port_8001):
    """Execute search_dates via Fli to get fare calendar."""
    agent = FlightAgent()

    start_date = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")
    end_date = (date.today() + timedelta(days=24)).strftime("%Y-%m-%d")

    result = agent.search_dates(
        origin="CCU",
        destination="BLR",
        start_date=start_date,
        end_date=end_date,
        trip_duration=3,
        is_round_trip=False,
        currency="INR",
    )

    assert result.get("success") is True, f"search_dates failed: {result.get('error')}"
    assert result.get("provider") == "fli"
    dates = result.get("dates", [])
    assert len(dates) > 0
    assert "price" in dates[0]
    assert "date" in dates[0]


# ---------------------------------------------------------------------------
# 7. Provider Fallback when Fli is offline
# ---------------------------------------------------------------------------
def test_provider_fallback_when_fli_offline(fli_server_port_8001):
    """Verify FlightAgent falls back to OctoTrip when Fli fails or is offline."""
    agent = FlightAgent()
    agent.clear_cache()

    dep_date = (date.today() + timedelta(days=17)).strftime("%Y-%m-%d")

    def mock_execute(agent_name, tool_name, arguments, user_confirmed=False):
        if tool_name.startswith("fli_") or tool_name == "fli":
            return {"success": False, "error": "Connection refused to Fli server on port 8001"}
        return {
            "success": True,
            "data": {
                "count": 1,
                "flights": [
                    {
                        "airline": "IndiGo",
                        "airline_code": "6E",
                        "flight_numbers": ["6E573"],
                        "is_direct": True,
                        "stops": 0,
                        "total_duration_minutes": 160,
                        "outbound": {
                            "departure": "CCU",
                            "arrival": "BLR",
                            "departure_time": "22:40",
                            "arrival_time": "01:20",
                            "departure_date": dep_date,
                            "arrival_date": dep_date,
                            "duration_minutes": 160,
                            "stops": 0,
                            "legs": [
                                {
                                    "flight_number": "6E573",
                                    "carrier": "IndiGo",
                                    "aircraft": "Airbus A321neo",
                                    "departure": "CCU",
                                    "arrival": "BLR",
                                    "departure_time": "22:40",
                                    "arrival_time": "01:20",
                                    "departure_date": dep_date,
                                    "arrival_date": dep_date,
                                    "duration_minutes": 160,
                                }
                            ],
                        },
                        "price": 8546.2,
                        "currency": "INR",
                        "booking_url": "https://mcp.octotrip.app/flights/test",
                    }
                ],
            },
        }

    with patch.object(remote_mcp_manager, "execute_tool", side_effect=mock_execute):
        result = agent.execute(
            departure_iata="CCU",
            arrival_iata="BLR",
            flight_date=dep_date,
            return_date=None,
            adults=1,
            currency="INR",
            bypass_cache=True,
        )

        assert result.success is True, f"Fallback search failed: {result.error}"
        assert result.data.get("provider") == "flight_octotrip", f"Expected octotrip fallback, got {result.data.get('provider')}"
        assert "OctoTrip" in result.summary


# ---------------------------------------------------------------------------
# 8. Both Flight Providers Unavailable Error Handling
# ---------------------------------------------------------------------------
def test_both_flight_providers_unavailable():
    """Verify that when both Fli and OctoTrip fail, an explicit error is returned without silent empty success."""
    agent = FlightAgent()
    agent.clear_cache()

    def mock_fail(agent_name, tool_name, arguments, user_confirmed=False):
        return {"success": False, "error": f"Simulated provider outage for {tool_name}"}

    with patch.object(remote_mcp_manager, "execute_tool", side_effect=mock_fail):
        result = agent.execute(
            departure_iata="CCU",
            arrival_iata="BLR",
            flight_date="2026-11-20",
            return_date=None,
            adults=1,
            currency="INR",
            bypass_cache=True,
        )

        assert result.success is False, "Expected success=False when both providers fail"
        assert result.data.get("provider") == "none"
        assert len(result.flights) == 0
        assert "Fli" in result.error or "OctoTrip" in result.error


# ---------------------------------------------------------------------------
# 9. Response Accuracy & Representation
# ---------------------------------------------------------------------------
def test_response_representation_and_attribution(fli_server_port_8001):
    """Verify the output accurately represents the flight metadata and attribution."""
    agent = FlightAgent()
    agent.clear_cache()

    dep_date = (date.today() + timedelta(days=17)).strftime("%Y-%m-%d")
    result = agent.execute(
        departure_iata="CCU",
        arrival_iata="BLR",
        flight_date=dep_date,
        adults=1,
        currency="INR",
        bypass_cache=True,
    )

    assert result.success is True
    assert "ranked_highlights" in result.data
    highlights = result.data["ranked_highlights"]
    assert "best_value" in highlights
    assert "cheapest" in highlights
    assert "fastest" in highlights
    assert highlights["best_value"]["price"] > 0
    assert "provider_display_name" in result.data
    assert result.data["provider_display_name"] == "Fli (Google Flights)"


# ---------------------------------------------------------------------------
# 10. Separate Outbound and Return Legs Search
# ---------------------------------------------------------------------------
def test_fli_separate_roundtrip_legs(fli_server_port_8001):
    """Verify executing separate outbound and inbound legs produces distinct sorted lists."""
    agent = FlightAgent()
    agent.clear_cache()

    dep_date = (date.today() + timedelta(days=17)).strftime("%Y-%m-%d")
    ret_date = (date.today() + timedelta(days=22)).strftime("%Y-%m-%d")

    res = agent.execute_separate_roundtrip_legs(
        departure_iata="CCU",
        arrival_iata="BLR",
        flight_date=dep_date,
        return_date=ret_date,
        adults=1,
        currency="INR",
        bypass_cache=True,
    )

    assert res["success"] is True
    outbound = res["outbound_flights"]
    returning = res["return_flights"]

    assert len(outbound) > 0, "Expected outbound flights"
    assert len(returning) > 0, "Expected return flights"

    # Verify cheapest flag is set on the first element of each leg
    assert outbound[0].get("is_lowest_price") is True
    assert returning[0].get("is_lowest_price") is True

    # Verify all outbound flights have direction='outbound'
    assert all(f.get("direction") == "outbound" for f in outbound)
    # Verify all return flights have direction='return'
    assert all(f.get("direction") == "return" for f in returning)

    # Verify outbound flights are sorted ascending by price
    outbound_prices = [float(f["price"]) for f in outbound]
    assert outbound_prices == sorted(outbound_prices)

    # Verify return flights are sorted ascending by price
    return_prices = [float(f["price"]) for f in returning]
    assert return_prices == sorted(return_prices)


