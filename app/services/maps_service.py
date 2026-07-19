import httpx
from loguru import logger

from app.config import (
    GEOAPIFY_API_KEY,
    GEOAPIFY_ROUTING_API_BASE_URL,
)
from app.services.geocoding_service import GeocodingService


class MapsService:
    """
    Handles communication with the Geoapify Routing API.
    """

    BASE_URL = GEOAPIFY_ROUTING_API_BASE_URL

    TRANSPORT_MODES = {
        "drive": "drive",
        "walk": "walk",
        "bicycle": "bicycle",
    }

    def __init__(self):
        self.api_key = GEOAPIFY_API_KEY
        self.geocoding_service = GeocodingService()

    def get_route(
        self,
        origin: str,
        destination: str,
        mode: str = "drive",
    ) -> dict:
        """
        Get route information between two places.
        """

        if not origin.strip():
            raise ValueError("Origin cannot be empty.")

        if not destination.strip():
            raise ValueError("Destination cannot be empty.")

        mode = mode.lower()

        if mode not in self.TRANSPORT_MODES:
            raise ValueError(
                f"Unsupported transport mode: {mode}"
            )

        origin_location = self.geocoding_service.get_coordinates(
            origin
        )

        destination_location = (
            self.geocoding_service.get_coordinates(
                destination
            )
        )

        waypoints = (
            f"{origin_location['latitude']},"
            f"{origin_location['longitude']}|"
            f"{destination_location['latitude']},"
            f"{destination_location['longitude']}"
        )

        params = {
            "waypoints": waypoints,
            "mode": self.TRANSPORT_MODES[mode],
            "apiKey": self.api_key,
        }

        try:

            with httpx.Client(timeout=20.0) as client:

                response = client.get(
                    self.BASE_URL,
                    params=params,
                )

                if response.status_code != 200:
                    try:
                        err_body = response.json()
                        err_msg = err_body.get("message")
                        if err_msg:
                            raise Exception(f"Geoapify API error message: {err_msg}")
                    except Exception as e:
                        if "Geoapify API error message" in str(e):
                            raise e

                response.raise_for_status()

                data = response.json()

            from app.schemas.api.response_models import MapsResponseModel
            validated = MapsResponseModel.model_validate(data)

            features = validated.features

            if not features:
                raise ValueError(
                    "No route found."
                )

            properties = features[0].properties

            distance = properties.distance
            time = properties.time

            instructions = []

            legs = properties.legs

            if legs:

                for step in legs[0].steps:

                    instructions.append(
                        {
                            "instruction": step.instruction,
                            "distance_m": step.distance,
                        }
                    )

            logger.info(
                f"Successfully calculated route "
                f"from {origin} to {destination}."
            )

            return {
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "distance_meters": distance,
                "distance_km": round(
                    distance / 1000,
                    2,
                ),
                "duration_seconds": time,
                "duration_minutes": round(
                    time / 60,
                    2,
                ),
                "instructions": instructions,
            }

        except httpx.HTTPStatusError as error:

            logger.error(
                f"Geoapify Routing API Error: "
                f"{error.response.text}"
            )

            raise Exception(
                "Unable to calculate route."
            ) from error

        except httpx.RequestError as error:

            logger.error(error)

            raise Exception(
                "Unable to connect to Geoapify."
            ) from error

        except Exception as error:

            logger.exception(error)

            raise