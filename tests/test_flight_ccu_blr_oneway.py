import os
import sys
import time
import requests
import subprocess
from datetime import date, timedelta
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from app.tools.flights import search_flights
from app.agents.flight.agent import FlightAgent


def _get(obj, key, default=None):
    """Helper to access properties from dict or Pydantic model uniformly."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _ensure_fli_server():
    """Ensure local Fli MCP server is running on port 8001 before executing search."""
    health_url = os.getenv("FLI_HEALTH_URL", "http://127.0.0.1:8001/health")
    try:
        r = requests.get(health_url, timeout=1)
        if r.status_code == 200:
            return None
    except Exception:
        pass

    proc = subprocess.Popen(
        ["uv", "run", "--no-sync", "python", "-m", "app.mcp.servers.fli_server"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for _ in range(30):
        try:
            r = requests.get(health_url, timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    return proc


def run_flight_check(flight_date: str = None):
    """
    Search one-way flights from Kolkata (CCU) to Bengaluru (BLR)
    using the Fli Google Flights / OctoTrip Flight MCP integration.
    """
    proc = _ensure_fli_server()

    if not flight_date:
        # Default to 17 days in future for active live scheduling
        flight_date = (date.today() + timedelta(days=17)).strftime("%Y-%m-%d")

    print("\n" + "=" * 95)
    print(f">> SEARCHING ONE-WAY FLIGHTS VIA MCP: CCU (Kolkata) -> BLR (Bengaluru)")
    print(f"Date: {flight_date} | Adults: 1 | Currency: INR | Trip Type: One-Way")
    print("=" * 95 + "\n")

    agent = FlightAgent()
    agent.clear_cache()
    result = agent.execute(
        departure_iata="CCU",
        arrival_iata="BLR",
        flight_date=flight_date,
        return_date=None,  # Strictly one-way
        adults=1,
        currency="INR",
        bypass_cache=True,
    )

    provider_name = result.data.get("provider_display_name") or result.data.get("provider") or "Unknown"
    print(f"Status Success : {result.success}")
    print(f"Provider Used  : {provider_name}")
    print(f"Error Message  : {result.error}")
    print(f"Execution Time : {result.execution_time_ms:.1f} ms")
    print(f"Total Offers   : {len(result.flights)}\n")

    if not result.success:
        print(f"[ERROR] Failed to fetch flights: {result.error}")
        return result

    print("-" * 95)
    print(f"{'#':<3} {'AIRLINE':<18} {'FLIGHT #':<12} {'DEP':<7} {'ARR':<7} {'STOPS':<10} {'DURATION':<10} {'PRICE (INR)':<14}")
    print("-" * 95)

    for idx, offer in enumerate(result.flights, 1):
        airline = _get(offer, "airline") or "Unknown"
        flight_numbers = _get(offer, "flight_numbers") or []
        primary_flight = _get(offer, "flight_number")
        if not flight_numbers and primary_flight:
            flight_numbers = [primary_flight]
        flight_no = ", ".join(flight_numbers) if flight_numbers else "N/A"

        dep_time = _get(offer, "departure_time") or "N/A"
        arr_time = _get(offer, "arrival_time") or "N/A"
        origin = _get(offer, "origin") or "CCU"
        destination = _get(offer, "destination") or "BLR"

        stops_count = _get(offer, "stops", 0)
        stops = f"{stops_count} stop(s)" if stops_count > 0 else "Non-stop"

        duration_mins = _get(offer, "total_duration_minutes", 0)
        formatted_duration = _get(offer, "duration_formatted")
        if formatted_duration:
            duration = formatted_duration
        elif duration_mins:
            duration = f"{duration_mins // 60}h {duration_mins % 60}m"
        else:
            duration = "N/A"

        price = _get(offer, "price", 0.0)
        price_str = f"INR {price:,.2f}"

        print(f"{idx:<3} {airline:<18} {flight_no:<12} {dep_time:<7} {arr_time:<7} {stops:<10} {duration:<10} {price_str:<14}")

        segments = _get(offer, "segments") or []
        if segments:
            print("    Segments:")
            for seg_idx, seg in enumerate(segments, 1):
                s_orig = _get(seg, "origin") or origin
                s_dest = _get(seg, "destination") or destination
                carrier = _get(seg, "carrier") or airline
                s_fnum = _get(seg, "flight_number") or flight_no
                aircraft = f" ({_get(seg, 'aircraft')})" if _get(seg, "aircraft") else ""
                s_dep = _get(seg, "departure_time") or ""
                s_arr = _get(seg, "arrival_time") or ""
                print(f"      [{seg_idx}] {carrier} {s_fnum}{aircraft}: {s_orig} ({s_dep}) -> {s_dest} ({s_arr})")

        booking_url = _get(offer, "booking_url")
        if booking_url:
            print(f"    Booking Link: {booking_url}")
        print("-" * 95)

    return result


def test_ccu_to_blr_oneway_flights():
    """Pytest test case to verify CCU -> BLR one-way flight search."""
    dep_date = (date.today() + timedelta(days=17)).strftime("%Y-%m-%d")
    result = run_flight_check(flight_date=dep_date)

    assert result.success is True, f"Flight search failed: {result.error}"
    assert len(result.flights) > 0, "No flight offers returned for CCU -> BLR"
    assert result.data.get("provider") == "fli"

    # Verify every flight is one-way, origin/dest matches, and critical fields are valid
    for idx, offer in enumerate(result.flights, 1):
        is_round_trip = _get(offer, "is_round_trip", False)
        assert is_round_trip is False, f"Offer {idx}: expected one-way flight"
        assert _get(offer, "origin") == "CCU", f"Offer {idx}: expected origin CCU"
        assert _get(offer, "destination") == "BLR", f"Offer {idx}: expected destination BLR"
        assert _get(offer, "currency") == "INR", f"Offer {idx}: expected currency INR"
        assert _get(offer, "price") > 0, f"Offer {idx}: expected positive price"
        assert _get(offer, "departure_time"), f"Offer {idx}: missing departure_time"
        assert _get(offer, "arrival_time"), f"Offer {idx}: missing arrival_time"
        assert _get(offer, "flight_number"), f"Offer {idx}: missing flight_number"
        assert _get(offer, "booking_url") and str(_get(offer, "booking_url")).startswith("http")


if __name__ == "__main__":
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    run_flight_check(flight_date=target_date)
