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
    currency: Optional[str] = "INR",
    limit: int = 10,
    **kwargs,
) -> ToolResult:
    """Search live flights using OctoTrip MCP by departure/arrival airport IATA codes, departure/return dates, passenger counts (adults, children, infants), cabin class ('Y' for economy, 'C' for business), and currency (defaults to INR)."""
    res = _get_flight_agent().execute(
        departure_iata=departure_iata,
        arrival_iata=arrival_iata,
        flight_date=flight_date,
        return_date=return_date,
        adults=adults,
        children=children,
        infants=infants,
        trip_class=trip_class,
        currency=currency,
        limit=limit,
        **kwargs,
    )
    if not res.success:
        return ToolResult(success=False, error=res.error or "Error searching flights", data=[])
    return ToolResult(success=True, data=res.flights)