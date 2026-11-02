import math
import httpx
from loguru import logger

from app.config import (
    GEOAPIFY_API_KEY,
    GEOAPIFY_ROUTING_API_BASE_URL,
)
from app.services.geocoding_service import GeocodingService


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great circle distance in kilometers between two points."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


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
        Get route information between two places with geographic sanity validation.
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

        # Great-circle distance check
        straight_line_km = haversine_distance_km(
            origin_location["latitude"],
            origin_location["longitude"],
            destination_location["latitude"],
            destination_location["longitude"],
        )

        # Reject impossible driving routes (e.g. crossing oceans or > 3000 km)
        if straight_line_km > 3000.0:
            logger.warning(
                f"Geographically impossible driving route requested from '{origin}' ({origin_location.get('country')}) "
                f"to '{destination}' ({destination_location.get('country')}): straight-line distance {straight_line_km:.1f} km."
            )
            return {
                "status": "no_route_found",
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "message": (
                    f"Direct driving route between '{origin}' and '{destination}' is geographically impossible "
                    f"(straight-line distance {straight_line_km:.1f} km across continents/oceans). Flight travel is required."
                ),
            }

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
                logger.warning(f"No driving route found between '{origin}' and '{destination}'.")
                return {
                    "status": "no_route_found",
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "message": f"No driving/transit route found between '{origin}' and '{destination}'. Direct long-distance flight or train travel recommended."
                }

            properties = features[0].properties

            distance = properties.distance
            time = properties.time
            distance_km = round(distance / 1000, 2)

            # Check if road distance is implausible compared to straight-line distance
            if distance_km > 3000.0 and straight_line_km < 1000.0:
                logger.warning(
                    f"Implausible route geometry detected between '{origin}' and '{destination}': "
                    f"road distance {distance_km} km vs straight-line {straight_line_km:.1f} km."
                )
                return {
                    "status": "no_route_found",
                    "origin": origin,
                    "destination": destination,
                    "mode": mode,
                    "message": (
                        f"Calculated road route ({distance_km} km) is geographically implausible for '{origin}' to '{destination}' "
                        f"(straight-line: {straight_line_km:.1f} km). Direct flights or trains recommended."
                    ),
                }

            instructions = []

            legs = properties.legs

            if legs:
                for step in legs[0].steps:
                    inst_text = step.instruction.get("text", "") if isinstance(step.instruction, dict) else str(step.instruction or "")
                    instructions.append(
                        {
                            "instruction": inst_text,
                            "distance_m": step.distance,
                        }
                    )

            logger.info(
                f"Successfully calculated route "
                f"from {origin} to {destination}."
            )

            return {
                "status": "success",
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

        except Exception as error:
            logger.warning(f"Geoapify Routing API gracefully handled error for {origin} -> {destination}: {error}")
            return {
                "status": "no_route_found",
                "origin": origin,
                "destination": destination,
                "mode": mode,
                "message": f"No direct driving route found between '{origin}' and '{destination}'. Recommend checking flight or train options."
            }