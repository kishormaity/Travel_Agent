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

                response.raise_for_status()

            data = response.json()

            flights = []

            for flight in data.get("data", []):

                flights.append(
                    {
                        "airline": flight.get("airline", {}).get("name"),
                        "flight_number": flight.get("flight", {}).get(
                            "number"
                        ),
                        "flight_iata": flight.get("flight", {}).get(
                            "iata"
                        ),
                        "flight_icao": flight.get("flight", {}).get(
                            "icao"
                        ),
                        "departure_airport": flight.get(
                            "departure", {}
                        ).get("airport"),
                        "departure_iata": flight.get(
                            "departure", {}
                        ).get("iata"),
                        "departure_terminal": flight.get(
                            "departure", {}
                        ).get("terminal"),
                        "departure_gate": flight.get(
                            "departure", {}
                        ).get("gate"),
                        "departure_scheduled": flight.get(
                            "departure", {}
                        ).get("scheduled"),
                        "arrival_airport": flight.get(
                            "arrival", {}
                        ).get("airport"),
                        "arrival_iata": flight.get(
                            "arrival", {}
                        ).get("iata"),
                        "arrival_terminal": flight.get(
                            "arrival", {}
                        ).get("terminal"),
                        "arrival_gate": flight.get(
                            "arrival", {}
                        ).get("gate"),
                        "arrival_scheduled": flight.get(
                            "arrival", {}
                        ).get("scheduled"),
                        "flight_status": flight.get("flight_status"),
                    }
                )

            logger.info(
                f"Found {len(flights)} flight(s)."
            )

            return flights

        except httpx.HTTPStatusError as error:

            logger.error(
                f"AviationStack API Error: {error.response.text}"
            )

            raise Exception(
                "Unable to retrieve flight information."
            ) from error

        except httpx.RequestError as error:

            logger.error(error)

            raise Exception(
                "Unable to connect to AviationStack."
            ) from error

        except Exception as error:

            logger.exception(error)

            raise