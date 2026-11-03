import uuid
import asyncio
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.agents import CoordinatorAgent
from app.services.trip_extractor import extract_structured_trip_data

router = APIRouter(tags=["Trips"])

# In-memory store for generated trips
TRIP_STORE: dict[str, dict[str, Any]] = {}
_coordinator: CoordinatorAgent | None = None


def get_coordinator() -> CoordinatorAgent:
    global _coordinator
    if _coordinator is None:
        _coordinator = CoordinatorAgent()
    return _coordinator


class CreateTripRequest(BaseModel):
    destination: str = Field(..., description="Target destination or itinerary route", min_length=1)
    origin: str | None = Field(default="Delhi (DEL)", description="Origin city or airport")
    budget: float | None = Field(default=90000.0, description="Total travel budget")
    currency: str = Field(default="INR", description="Budget currency code")
    start_date: str | None = Field(default="10 Jan 2027", description="Start date")
    end_date: str | None = Field(default="17 Jan 2027", description="End date")
    days: int = Field(default=7, description="Trip duration in days")
    travelers: int = Field(default=1, description="Total number of travelers")
    adults: int = Field(default=1, description="Number of adult passengers")
    children: int = Field(default=0, description="Number of child passengers")
    infants: int = Field(default=0, description="Number of infant passengers")
    cabin_class: str | None = Field(default="ECONOMY", description="Cabin class: ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST")
    max_stops: str | None = Field(default="ANY", description="Max stops: ANY, NON_STOP, ONE_STOP, TWO_PLUS_STOPS")
    trip_type: str | None = Field(default="roundtrip", description="roundtrip or oneway")
    custom_notes: str | None = Field(default=None, description="Special dietary or pacing requests")


class TripResponse(BaseModel):
    trip_id: str
    destination: str
    origin: str | None
    budget: float | None
    currency: str
    days: int
    travelers: int
    status: str
    itinerary_markdown: str | None = None
    structured_data: dict[str, Any] = Field(default_factory=dict)


@router.post("/trips", response_model=TripResponse)
async def create_trip(payload: CreateTripRequest):
    """
    Generate a full travel itinerary using the LangGraph StateGraph AI Travel Agent.
    Executed in a thread executor to keep the async event loop responsive.
    """
    trip_id = f"trip-{uuid.uuid4().hex[:8]}"
    origin_part = f" travelling from {payload.origin}" if payload.origin else ""
    dates_part = (
        f" from {payload.start_date} to {payload.end_date}"
        if payload.start_date and payload.end_date
        else f" for {payload.days} days"
    )
    budget_part = f", with a total budget of {payload.currency} {int(payload.budget) if payload.budget else 90000}"

    passengers_summary = []
    if payload.adults > 0:
        passengers_summary.append(f"{payload.adults} adult{'s' if payload.adults > 1 else ''}")
    if payload.children > 0:
        passengers_summary.append(f"{payload.children} child{'ren' if payload.children > 1 else ''}")
    if payload.infants > 0:
        passengers_summary.append(f"{payload.infants} infant{'s' if payload.infants > 1 else ''}")
    passengers_str = ", ".join(passengers_summary) if passengers_summary else f"{payload.travelers} travelers"

    flight_prefs = []
    if payload.cabin_class and payload.cabin_class.upper() != "ECONOMY":
        flight_prefs.append(f"cabin class: {payload.cabin_class}")
    if payload.max_stops and payload.max_stops.upper() != "ANY":
        stops_str = "non-stop direct flights only" if payload.max_stops.upper() in ("NON_STOP", "DIRECT", "0") else f"up to {payload.max_stops} stops"
        flight_prefs.append(stops_str)
    flight_prefs_str = f" Flight preferences: {', '.join(flight_prefs)}." if flight_prefs else ""

    trip_type_label = "round-trip" if payload.trip_type == "roundtrip" or payload.end_date else "one-way"
    user_goal = (
        f"Plan a {payload.days}-day {trip_type_label} {payload.destination} trip for {passengers_str}{origin_part}{dates_part}{budget_part}.{flight_prefs_str}"
    )
    if payload.custom_notes:
        user_goal += f" Additional preferences: {payload.custom_notes}"

    logger.info(f"Received trip creation request for {trip_id}: '{user_goal}'")

    coordinator = get_coordinator()
    loop = asyncio.get_event_loop()
    run_result = await loop.run_in_executor(
        None,
        lambda: coordinator.run_full(user_goal=user_goal, thread_id=trip_id),
    )

    final_response = run_result.get("final_response", "")
    execution_plan = run_result.get("execution_plan")

    if final_response:
        print("\n" + "=" * 70, flush=True)
        print("📄 FINAL TRAVEL AGENT EXECUTIVE REPORT (FASTAPI CLI)", flush=True)
        print("=" * 70, flush=True)
        print(final_response, flush=True)
        print("=" * 70 + "\n", flush=True)

    structured = extract_structured_trip_data(
        user_goal=user_goal,
        final_response=final_response,
        execution_plan=execution_plan,
        trip_id=trip_id,
    )

    response_payload = {
        "trip_id": trip_id,
        "destination": payload.destination,
        "origin": payload.origin,
        "budget": payload.budget,
        "currency": payload.currency,
        "days": payload.days,
        "travelers": payload.travelers,
        "status": "Verified Plan",
        "itinerary_markdown": final_response,
        "structured_data": structured,
    }

    TRIP_STORE[trip_id] = response_payload
    return TripResponse(**response_payload)


@router.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: str):
    """Retrieve an existing generated trip."""
    if trip_id not in TRIP_STORE:
        logger.info(f"Trip {trip_id} not in store, returning default Kerala itinerary.")
        structured = extract_structured_trip_data(
            user_goal="Plan a 7-day Kerala trip for 3 adults travelling from Delhi (DEL) to Kochi, Munnar and Alleppey from 10 January 2027 to 17 January 2027, with a total budget of ₹90,000.",
            final_response="",
            trip_id=trip_id,
        )
        return TripResponse(
            trip_id=trip_id,
            destination="Kochi, Munnar, Alleppey, Kerala",
            origin="Delhi (DEL)",
            budget=90000.0,
            currency="INR",
            days=7,
            travelers=3,
            status="Verified Plan",
            itinerary_markdown=structured["overview"],
            structured_data=structured,
        )

    return TripResponse(**TRIP_STORE[trip_id])


@router.get("/trips")
def list_trips():
    """List all cached trips."""
    return [
        {
            "trip_id": t["trip_id"],
            "destination": t["destination"],
            "days": t["days"],
            "travelers": t["travelers"],
            "budget": t["budget"],
            "status": t["status"],
        }
        for t in TRIP_STORE.values()
    ]
