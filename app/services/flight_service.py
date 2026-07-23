import httpx
from loguru import logger

from app.config import (
    AVIATIONSTACK_API_KEY,
    AVIATIONSTACK_API_BASE_URL,
)


class FlightService:
    """
    Handles communication with the AviationStack API.
    """

    BASE_URL = AVIATIONSTACK_API_BASE_URL

    def __init__(self):
        self.api_key = AVIATIONSTACK_API_KEY

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
        Search flights using the AviationStack API.

        Args:
            departure_iata: Departure airport IATA code.
            arrival_iata: Arrival airport IATA code.
            flight_number: Flight number.
            airline_iata: Airline IATA code.
            flight_date: YYYY-MM-DD.
            limit: Maximum number of results.

        Returns:
            List of flight information.
        """

        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        params = {
            "access_key": self.api_key,
            "limit": limit,
        }

        if departure_iata:
            params["dep_iata"] = departure_iata.upper()

        if arrival_iata:
            params["arr_iata"] = arrival_iata.upper()

        if airline_iata:
            params["airline_iata"] = airline_iata.upper()

        if flight_number:
            params["flight_number"] = flight_number

        if flight_date:
            params["flight_date"] = flight_date

        try:

            with httpx.Client(timeout=15.0) as client:

                response = client.get(
                    f"{self.BASE_URL}/flights",
                    params=params,
                )

                if response.status_code != 200:
                    try:
                        err_body = response.json()
                        err_msg = err_body.get("error", {}).get("message") or err_body.get("error", {}).get("info")
                        if err_msg:
                            raise Exception(f"AviationStack API error message: {err_msg}")
                    except Exception as e:
                        if "AviationStack API error message" in str(e):
                            raise e

                response.raise_for_status()

                data = response.json()

                if isinstance(data, dict) and "error" in data:
                    err_msg = data.get("error", {}).get("message") or data.get("error", {}).get("info")
                    if err_msg:
                        raise Exception(f"AviationStack API error message: {err_msg}")

                from app.schemas.api.response_models import FlightResponseModel
                validated = FlightResponseModel.model_validate(data)

            flights = []

            from datetime import datetime
            today_str = datetime.now().strftime("%Y-%m-%d")

            for flight in validated.data:
                # If flight_date was not specified, filter out past flights
                if not flight_date:
                    if flight.departure and flight.departure.scheduled:
                        dep_date = flight.departure.scheduled[:10]
                        if dep_date < today_str:
                            continue

                flights.append(
                    {
                        "airline": flight.airline.name if flight.airline else None,
                        "flight_number": flight.flight.number if flight.flight else None,
                        "flight_iata": flight.flight.iata if flight.flight else None,
                        "flight_icao": flight.flight.icao if flight.flight else None,
                        "departure_airport": flight.departure.airport if flight.departure else None,
                        "departure_iata": flight.departure.iata if flight.departure else None,
                        "departure_terminal": flight.departure.terminal if flight.departure else None,
                        "departure_gate": flight.departure.gate if flight.departure else None,
                        "departure_scheduled": flight.departure.scheduled if flight.departure else None,
                        "arrival_airport": flight.arrival.airport if flight.arrival else None,
                        "arrival_iata": flight.arrival.iata if flight.arrival else None,
                        "arrival_terminal": flight.arrival.terminal if flight.arrival else None,
                        "arrival_gate": flight.arrival.gate if flight.arrival else None,
                        "arrival_scheduled": flight.arrival.scheduled if flight.arrival else None,
                        "flight_status": flight.flight_status,
                    }
                )

            logger.info(
                f"Found {len(flights)} flight(s)."
            )

            return flights

        except Exception as error:
            logger.warning(f"AviationStack API flight search encountered error: {error}. Returning empty flight list.")
            return []