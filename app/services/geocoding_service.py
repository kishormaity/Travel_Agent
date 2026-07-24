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

            from app.schemas.api.response_models import GeocodingResponseModel
            validated = GeocodingResponseModel.model_validate(data)

            features = validated.features

            if not features and ", India" not in city:
                params["text"] = f"{city}, India"
                with httpx.Client(timeout=10.0) as client:
                    res2 = client.get(self.BASE_URL, params=params)
                    if res2.status_code == 200:
                        data2 = res2.json()
                        validated2 = GeocodingResponseModel.model_validate(data2)
                        features = validated2.features

            if not features:
                raise ValueError(
                    f"No location found for '{city}'."
                )

            properties = features[0].properties

            logger.info(
                f"Successfully geocoded '{city}'."
            )

            return {
                "place_id": properties.place_id,
                "city": properties.city,
                "state": properties.state,
                "country": properties.country,
                "country_code": properties.country_code,
                "postcode": properties.postcode,
                "formatted_address": properties.formatted,
                "latitude": properties.lat,
                "longitude": properties.lon,
                "timezone": properties.timezone.name if properties.timezone else None,
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