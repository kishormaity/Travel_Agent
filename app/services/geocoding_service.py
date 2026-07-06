import httpx
from loguru import logger

from app.config import GEOAPIFY_API_KEY


class GeocodingService:
    """
    Handles communication with the Geoapify Geocoding API.
    """

    BASE_URL = "https://api.geoapify.com/v1/geocode/search"

    def __init__(self):
        self.api_key = GEOAPIFY_API_KEY

    def get_coordinates(
        self,
        city: str,
    ) -> dict:
        """
        Convert a city name into latitude and longitude.
        """

        if not city.strip():
            raise ValueError("City cannot be empty.")

        params = {
            "text": city,
            "limit": 1,
            "apiKey": self.api_key,
        }

        try:

            with httpx.Client(
                timeout=10.0,
            ) as client:

                response = client.get(
                    self.BASE_URL,
                    params=params,
                )

                response.raise_for_status()

            data = response.json()

            features = data.get("features", [])

            if not features:
                raise ValueError(
                    f"No location found for '{city}'."
                )

            properties = features[0]["properties"]

            logger.info(
                f"Successfully geocoded '{city}'."
            )

            return {
                "place_id": properties.get("place_id"),
                "city": properties.get("city"),
                "state": properties.get("state"),
                "country": properties.get("country"),
                "country_code": properties.get("country_code"),
                "postcode": properties.get("postcode"),
                "formatted_address": properties.get("formatted"),
                "latitude": properties.get("lat"),
                "longitude": properties.get("lon"),
                "timezone": properties.get("timezone", {}).get("name"),
            }

        except httpx.HTTPStatusError as error:

            logger.error(
                f"Geoapify Geocoding API Error: {error.response.text}"
            )

            raise Exception(
                f"Unable to geocode '{city}'."
            ) from error

        except httpx.RequestError as error:

            logger.error(error)

            raise Exception(
                "Unable to connect to Geoapify."
            ) from error

        except Exception as error:

            logger.exception(error)

            raise