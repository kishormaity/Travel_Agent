from loguru import logger

from app.services.flight_service import FlightService


class FlightTool:
    """
    Tool responsible for searching flights.
    """

    def __init__(self):
        self.flight_service = FlightService()

    def search_flights(
        self,
        departure_iata: str | None = None,
        arrival_iata: str | None = None,
        flight_number: str | None = None,
        airline_iata: str | None = None,
        flight_date: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search flights using AviationStack.

        Args:
            departure_iata: Departure airport IATA code.
            arrival_iata: Arrival airport IATA code.
            flight_number: Flight number.
            airline_iata: Airline IATA code.
            flight_date: Flight date (YYYY-MM-DD).
            limit: Maximum number of results.

        Returns:
            List of flights.
        """

        logger.info(
            "Flight Tool invoked "
            f"(departure={departure_iata}, "
            f"arrival={arrival_iata}, "
            f"flight_number={flight_number}, "
            f"airline={airline_iata}, "
            f"date={flight_date})"
        )

        return self.flight_service.search_flights(
            departure_iata=departure_iata,
            arrival_iata=arrival_iata,
            flight_number=flight_number,
            airline_iata=airline_iata,
            flight_date=flight_date,
            limit=limit,
        )