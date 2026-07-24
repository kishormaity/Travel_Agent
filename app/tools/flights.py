from loguru import logger
from langchain_core.tools import tool
from app.services.flight_service import FlightService
from app.schemas.tool_result import ToolResult

_flight_service = FlightService()


@tool
def search_flights(
    departure_iata: str | None = None,
    arrival_iata: str | None = None,
    flight_number: str | None = None,
    airline_iata: str | None = None,
    flight_date: str | None = None,
    limit: int = 10,
) -> ToolResult:
    """Search flights using AviationStack by departure/arrival airport IATA codes or flight date."""
    logger.info(
        f"Flight Tool invoked (departure={departure_iata}, arrival={arrival_iata}, date={flight_date})"
    )
    try:
        data = _flight_service.search_flights(
            departure_iata=departure_iata,
            arrival_iata=arrival_iata,
            flight_number=flight_number,
            airline_iata=airline_iata,
            flight_date=flight_date,
            limit=limit,
        )
        return ToolResult(success=True, data=data)
    except Exception as e:
        logger.warning(f"Flight Tool failed: {e}")
        return ToolResult(success=False, error=str(e), data=[])


class FlightTool:
    def search_flights(
        self,
        departure_iata: str | None = None,
        arrival_iata: str | None = None,
        flight_number: str | None = None,
        airline_iata: str | None = None,
        flight_date: str | None = None,
        limit: int = 10,
    ) -> ToolResult:
        return search_flights.invoke({
            "departure_iata": departure_iata,
            "arrival_iata": arrival_iata,
            "flight_number": flight_number,
            "airline_iata": airline_iata,
            "flight_date": flight_date,
            "limit": limit,
        })