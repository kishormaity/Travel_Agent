import pytest
from app.agents.flight.agent import FlightAgent
from app.agents.flight.normalizer import (
    normalize_octotrip_flight,
    rank_flight_offers,
    _validate_airport_route,
)
from app.schemas.flight import NormalizedFlightOffer


# 1. Valid Round Trip Test
def test_valid_round_trip():
    raw_item = {
        "airline": "IndiGo",
        "price": 35626.61,
        "currency": "INR",
        "baggage": "15 kg included",
        "booking_url": "https://octotrip.app/book/ind123",
        "outbound": {
            "departure": "CCU",
            "arrival": "GOI",
            "departure_date": "2026-12-15",
            "departure_time": "08:00",
            "arrival_date": "2026-12-15",
            "arrival_time": "13:30",
            "duration_minutes": 330,
            "stops": 1,
            "legs": [
                {
                    "carrier": "IndiGo",
                    "flight_number": "6E-101",
                    "departure": "CCU",
                    "arrival": "BOM",
                    "departure_date": "2026-12-15",
                    "departure_time": "08:00",
                    "arrival_date": "2026-12-15",
                    "arrival_time": "10:30",
                    "duration_minutes": 150,
                },
                {
                    "carrier": "IndiGo",
                    "flight_number": "6E-202",
                    "departure": "BOM",
                    "arrival": "GOI",
                    "departure_date": "2026-12-15",
                    "departure_time": "12:00",
                    "arrival_date": "2026-12-15",
                    "arrival_time": "13:30",
                    "duration_minutes": 90,
                },
            ],
        },
        "return": {
            "departure": "GOI",
            "arrival": "CCU",
            "departure_date": "2026-12-20",
            "departure_time": "15:00",
            "arrival_date": "2026-12-20",
            "arrival_time": "18:00",
            "duration_minutes": 180,
            "stops": 0,
            "legs": [
                {
                    "carrier": "IndiGo",
                    "flight_number": "6E-303",
                    "departure": "GOI",
                    "arrival": "CCU",
                    "departure_date": "2026-12-20",
                    "departure_time": "15:00",
                    "arrival_date": "2026-12-20",
                    "arrival_time": "18:00",
                    "duration_minutes": 180,
                }
            ],
        },
    }

    offer = normalize_octotrip_flight(raw_item, origin_hint="CCU", dest_hint="GOI")

    assert offer.is_round_trip is True
    assert len(offer.segments) == 2
    assert len(offer.inbound_segments) == 1
    assert offer.outbound_duration_minutes == 330
    assert offer.outbound_duration_minutes == 330
    assert offer.inbound_duration_minutes == 180
    assert offer.outbound_duration_formatted == "5h 30m"
    assert offer.inbound_duration_formatted == "3h 0m"
    assert "Outbound: 5h 30m" in offer.duration_formatted
    assert "Return: 3h 0m" in offer.duration_formatted
    assert offer.total_round_trip_price == 35626.61
    assert offer.route_match is True
    assert offer.booking_url == "https://octotrip.app/book/ind123"
    assert offer.baggage == "15 kg included"


# 2. One-Way Journey Test
def test_one_way_journey():
    raw_item = {
        "airline": "Air India",
        "price": 12000.0,
        "currency": "INR",
        "outbound": {
            "departure": "CCU",
            "arrival": "GOI",
            "departure_date": "2026-12-15",
            "departure_time": "09:00",
            "arrival_date": "2026-12-15",
            "arrival_time": "12:00",
            "duration_minutes": 180,
            "stops": 0,
            "legs": [
                {
                    "carrier": "Air India",
                    "flight_number": "AI-404",
                    "departure": "CCU",
                    "arrival": "GOI",
                    "departure_date": "2026-12-15",
                    "departure_time": "09:00",
                    "arrival_date": "2026-12-15",
                    "arrival_time": "12:00",
                    "duration_minutes": 180,
                }
            ],
        },
    }

    offer = normalize_octotrip_flight(raw_item, origin_hint="CCU", dest_hint="GOI")

    assert offer.is_round_trip is False
    assert len(offer.segments) == 1
    assert len(offer.inbound_segments) == 0
    assert offer.total_round_trip_price is None
    assert offer.price == 12000.0
    assert offer.total_duration_minutes == 180
    assert offer.duration_formatted == "3h 0m"
    assert offer.outbound_duration_formatted == "3h 0m"
    assert offer.inbound_duration_formatted == ""


# 3. Different Outbound and Return Airports
def test_different_outbound_and_return_airports():
    raw_item = {
        "airline": "SpiceJet",
        "price": 28000.0,
        "outbound": {
            "departure": "CCU",
            "arrival": "GOI",
            "legs": [{"departure": "CCU", "arrival": "GOI", "duration_minutes": 200}],
        },
        "return": {
            "departure": "GOI",
            "arrival": "DEL",  # Returned to Delhi instead of Kolkata
            "legs": [{"departure": "GOI", "arrival": "DEL", "duration_minutes": 150}],
        },
    }

    offer = normalize_octotrip_flight(raw_item, origin_hint="CCU", dest_hint="GOI")

    assert offer.is_round_trip is True
    assert offer.route_match is False
    assert "Return destination mismatch" in (offer.airport_notes or "")


# 4. Incorrect or Missing Inbound Segments
def test_incorrect_or_missing_inbound_segments():
    raw_item = {
        "airline": "Vistara",
        "price": 22000.0,
        "outbound": {
            "departure": "CCU",
            "arrival": "GOI",
            "legs": [{"departure": "CCU", "arrival": "GOI", "duration_minutes": 240}],
        },
        "return": {"legs": []},
    }

    offer = normalize_octotrip_flight(raw_item, origin_hint="CCU", dest_hint="GOI")

    assert offer.is_round_trip is False
    assert len(offer.inbound_segments) == 0
    assert offer.total_round_trip_price is None


# 5. Duration Calculation Test
def test_duration_calculation():
    raw_item = {
        "airline": "IndiGo",
        "price": 30000.0,
        "outbound": {
            "duration_minutes": 315,
            "legs": [
                {"departure": "CCU", "arrival": "HYD", "duration_minutes": 120},
                {"departure": "HYD", "arrival": "GOI", "duration_minutes": 90},
            ],
        },
        "return": {
            "duration_minutes": 245,
            "legs": [{"departure": "GOI", "arrival": "CCU", "duration_minutes": 245}],
        },
    }

    offer = normalize_octotrip_flight(raw_item, origin_hint="CCU", dest_hint="GOI")

    assert offer.outbound_duration_minutes == 315
    assert offer.outbound_duration_formatted == "5h 15m"
    assert offer.inbound_duration_minutes == 245
    assert offer.inbound_duration_formatted == "4h 5m"
    assert "Outbound: 5h 15m" in offer.duration_formatted
    assert "Return: 4h 5m" in offer.duration_formatted


# 6. Ranking Correctness Test
def test_ranking_correctness():
    offer1 = NormalizedFlightOffer(
        provider="octotrip",
        provider_flight_id="f1",
        airline="Airline Cheap",
        origin="CCU",
        destination="GOI",
        departure_time="08:00",
        arrival_time="18:00",
        total_duration_minutes=600,
        total_stops=2,
        price=20000.0,
    )
    offer2 = NormalizedFlightOffer(
        provider="octotrip",
        provider_flight_id="f2",
        airline="Airline Fast",
        origin="CCU",
        destination="GOI",
        departure_time="10:00",
        arrival_time="13:00",
        total_duration_minutes=180,
        total_stops=0,
        price=50000.0,
    )
    offer3 = NormalizedFlightOffer(
        provider="octotrip",
        provider_flight_id="f3",
        airline="Airline Balanced",
        origin="CCU",
        destination="GOI",
        departure_time="09:00",
        arrival_time="13:30",
        total_duration_minutes=270,
        total_stops=0,
        price=25000.0,
    )

    ranked = rank_flight_offers([offer1, offer2, offer3])

    assert ranked["cheapest"][0].airline == "Airline Cheap"
    assert ranked["fastest"][0].airline == "Airline Fast"
    assert ranked["fewest_stops"][0].total_stops == 0
    assert ranked["best_value"][0].airline == "Airline Balanced"


# 7. Airport Mismatch: GOI vs GOX Distinction
def test_airport_mismatch_goi_vs_gox():
    raw_item = {
        "airline": "Akasa Air",
        "price": 18000.0,
        "outbound": {
            "departure": "CCU",
            "arrival": "GOX",
            "legs": [{"departure": "CCU", "arrival": "GOX", "duration_minutes": 190}],
        },
    }

    offer = normalize_octotrip_flight(raw_item, origin_hint="CCU", dest_hint="GOI")

    assert offer.route_match is False
    assert "Dabolim Airport (GOI" in offer.airport_notes
    assert "Manohar International Airport (GOX" in offer.airport_notes
    assert "60km apart" in offer.airport_notes


# 8. Malformed Provider Response
def test_malformed_provider_response():
    raw_item = {
        "airline": None,
        "price": "not_a_number",
        "outbound": None,
        "return": None,
    }

    offer = normalize_octotrip_flight(raw_item, origin_hint="CCU", dest_hint="GOI")

    assert offer.airline == "Unknown"
    assert offer.price is None
    assert offer.is_round_trip is False
    assert offer.segments == []
    assert "baggage" in offer.missing_fields
    assert "price_verification_timestamp" in offer.missing_fields
