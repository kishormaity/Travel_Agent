from typing import Optional
from langchain_core.tools import tool
from app.schemas.tool_result import ToolResult

_flight_agent = None


def _get_flight_agent():
    global _flight_agent
    if _flight_agent is None:
        from app.agents.flight.agent import FlightAgent
        _flight_agent = FlightAgent()
    return _flight_agent


@tool
def search_flights(
    departure_iata: Optional[str] = None,
    arrival_iata: Optional[str] = None,
    flight_date: Optional[str] = None,
    return_date: Optional[str] = None,
    adults: int = 1,
    children: int = 0,
    infants: int = 0,
    trip_class: str = "Y",
    cabin_class: Optional[str] = None,
    max_stops: Optional[str] = "ANY",
    currency: Optional[str] = "INR",
    **kwargs,
) -> ToolResult:
    """Search live flights using Fli Google Flights or OctoTrip MCP by departure/arrival airport IATA codes, departure/return dates, passenger counts (adults, children, infants), cabin class ('ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST'), max_stops ('ANY', 'NON_STOP', 'ONE_STOP', 'TWO_PLUS_STOPS'), and currency (defaults to INR)."""
    agent = _get_flight_agent()
    effective_cabin = cabin_class or trip_class or "Y"
    if return_date:
        res_dict = agent.execute_separate_roundtrip_legs(
            departure_iata=departure_iata,
            arrival_iata=arrival_iata,
            flight_date=flight_date,
            return_date=return_date,
            adults=adults,
            children=children,
            infants=infants,
            trip_class=effective_cabin,
            cabin_class=effective_cabin,
            max_stops=max_stops,
            currency=currency,
            **kwargs,
        )
        all_flights = res_dict.get("all_flights", [])
        notice = res_dict.get("notice") or "No flights found matching requested criteria."
        if not all_flights:
            return ToolResult(
                success=True,
                data=[],
                metadata={"notice": notice, "status": "NOT_FOUND"}
            )
        return ToolResult(success=True, data=all_flights)

    res = agent.execute(
        departure_iata=departure_iata,
        arrival_iata=arrival_iata,
        flight_date=flight_date,
        return_date=None,
        adults=adults,
        children=children,
        infants=infants,
        trip_class=effective_cabin,
        cabin_class=effective_cabin,
        max_stops=max_stops,
        currency=currency,
        **kwargs,
    )
    if not res.flights:
        notice = res.summary or "No flights found matching requested criteria."
        return ToolResult(
            success=True,
            data=[],
            metadata={"notice": notice, "status": "NOT_FOUND"}
        )
    return ToolResult(success=True, data=res.flights)


@tool
def search_flight_dates(
    origin: str,
    destination: str,
    start_date: str,
    end_date: str,
    trip_duration: int = 3,
    is_round_trip: bool = False,
    currency: str = "INR",
    **kwargs,
) -> ToolResult:
    """Explore cheapest flight fares across a date range using the Fli Google Flights MCP date calendar tool."""
    res = _get_flight_agent().search_dates(
        origin=origin,
        destination=destination,
        start_date=start_date,
        end_date=end_date,
        trip_duration=trip_duration,
        is_round_trip=is_round_trip,
        currency=currency,
        **kwargs,
    )
    if not res.get("success"):
        return ToolResult(success=False, error=res.get("error") or "Error searching flight dates", data=[])
    return ToolResult(success=True, data=res.get("dates", []))
