import uuid
import asyncio
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from loguru import logger

from app.agents import CoordinatorAgent
from app.services.trip_extractor import extract_structured_trip_data
from app.core.latency_profiler import LatencyProfiler

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
    latency: dict[str, Any] | None = None


@router.post("/trips", response_model=TripResponse)
async def create_trip(payload: CreateTripRequest):
    """
    Generate a full travel itinerary using the LangGraph StateGraph AI Travel Agent.
    Executed in a thread executor to keep the async event loop responsive.
    """
    trip_id = f"trip-{uuid.uuid4().hex[:8]}"
    profiler = LatencyProfiler(trace_id=trip_id)

    # Extract & resolve Destination & Origin directly from input boxes
    from app.services.request_normalizer import KNOWN_AIRPORTS, CITY_TO_AIRPORT

    dest_raw = str(payload.destination).strip()
    dest_upper = dest_raw.upper()
    if dest_upper in KNOWN_AIRPORTS:
        dest_display = f"{KNOWN_AIRPORTS[dest_upper][0]} ({dest_upper})"
    elif dest_raw.lower() in CITY_TO_AIRPORT:
        iata = CITY_TO_AIRPORT[dest_raw.lower()]
        dest_display = f"{dest_raw.title()} ({iata})"
    else:
        dest_display = dest_raw

    orig_raw = str(payload.origin or "Delhi (DEL)").strip()
    orig_upper = orig_raw.upper()[:3]
    if orig_upper in KNOWN_AIRPORTS:
        orig_display = f"{KNOWN_AIRPORTS[orig_upper][0]} ({orig_upper})"
    else:
        orig_display = orig_raw

    passengers_summary = []
    if payload.adults > 0:
        passengers_summary.append(f"{payload.adults} adult{'s' if payload.adults > 1 else ''}")
    if payload.children > 0:
        passengers_summary.append(f"{payload.children} child{'ren' if payload.children > 1 else ''}")
    if payload.infants > 0:
        passengers_summary.append(f"{payload.infants} infant{'s' if payload.infants > 1 else ''}")
    passengers_str = ", ".join(passengers_summary) if passengers_summary else f"{payload.travelers} travelers"

    trip_type_label = "round-trip" if payload.trip_type == "roundtrip" or payload.end_date else "one-way"

    # Cabin class display (always explicit)
    cabin_str = (payload.cabin_class or "Economy").replace("_", " ").title()

    # Flight stops display (always explicit)
    if payload.max_stops and payload.max_stops.upper() in ("NON_STOP", "DIRECT", "0"):
        stops_str = "Non-Stop direct flights only"
    elif payload.max_stops and payload.max_stops.upper() in ("ONE_STOP", "1"):
        stops_str = "Up to 1 stop"
    elif payload.max_stops and payload.max_stops.upper() in ("TWO_PLUS_STOPS", "2"):
        stops_str = "Up to 2 stops"
    else:
        stops_str = "Any Stops"

    dates_str = (
        f"{payload.start_date} to {payload.end_date} ({payload.days} days)"
        if payload.start_date and payload.end_date
        else f"{payload.days} days"
    )

    budget_val = int(payload.budget) if payload.budget else 90000

    user_goal = (
        f"Trip Planning Request from Form Input:\n"
        f"- Target Destination: {dest_display}\n"
        f"- Departure Origin: {orig_display}\n"
        f"- Travel Dates: {dates_str}\n"
        f"- Trip Type: {trip_type_label}\n"
        f"- Travelers: {passengers_str}\n"
        f"- Cabin Class: {cabin_str}\n"
        f"- Flight Stops: {stops_str}\n"
        f"- Total Budget: {payload.currency} {budget_val}"
    )
    if payload.custom_notes:
        user_goal += f"\n- Special Notes: {payload.custom_notes}"

    logger.info(
        f"Received trip creation request for {trip_id}: {dest_display} from {orig_display} "
        f"({dates_str}, {passengers_str}, Cabin: {cabin_str}, Stops: {stops_str}, Budget: {payload.currency} {budget_val})"
    )

    profiler.mark("request_preparation")

    coordinator = get_coordinator()
    loop = asyncio.get_event_loop()
    run_result = await loop.run_in_executor(
        None,
        lambda: coordinator.run_full(user_goal=user_goal, thread_id=trip_id),
    )
    profiler.mark("graph_execution")

    final_response = run_result.get("final_response", "")
    execution_plan = run_result.get("execution_plan")

    if execution_plan and hasattr(execution_plan, "tasks"):
        for t_id, task in execution_plan.tasks.items():
            if task.execution_time:
                profiler.record_tool(f"{task.tool_name} (Task #{t_id})", task.execution_time)
            elif task.started_at and task.finished_at:
                profiler.record_tool(f"{task.tool_name} (Task #{t_id})", task.finished_at - task.started_at)

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
    profiler.mark("structured_extraction")

    if not structured or (not structured.get("destinations") and not structured.get("itinerary") and not structured.get("flights") and not final_response):
        logger.warning(f"Backend failed to synthesize data for trip {trip_id}.")
        raise HTTPException(
            status_code=502,
            detail="No data returned from backend.",
        )

    latency_summary = profiler.get_summary()
    profiler.print_audit_report()

    # Surface latency metrics in structured_data and payload
    structured["latency"] = latency_summary

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
        "latency": latency_summary,
    }

    TRIP_STORE[trip_id] = response_payload
    return TripResponse(**response_payload)


@router.get("/trips/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: str):
    """Retrieve an existing generated trip."""
    if trip_id not in TRIP_STORE:
        logger.warning(f"Trip {trip_id} not found in store.")
        raise HTTPException(
            status_code=404,
            detail="Trip not found. No data returned from backend.",
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
