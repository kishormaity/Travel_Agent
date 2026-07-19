import httpx
from loguru import logger

from app.config import GEOAPIFY_API_KEY
from app.config import GEOAPIFY_API_BASE_URL
from app.services.geocoding_service import GeocodingService


class PlacesService:
    """
    Handles communication with the Geoapify Places API.
    """

    BASE_URL = GEOAPIFY_API_BASE_URL

    CATEGORY_MAPPING = {
        "restaurant": "catering.restaurant",
        "cafe": "catering.cafe",
        "hotel": "accommodation.hotel",
        "airport": "airport",
        "hospital": "healthcare.hospital",
        "atm": "service.financial.atm",
        "museum": "entertainment.museum",
        "tourist_attraction": "tourism.attraction",
        "shopping_mall": "commercial.shopping_mall",
        "bus_station": "public_transport.bus",
        "train_station": "public_transport.train",
    }

    def __init__(self):
        self.api_key = GEOAPIFY_API_KEY
        self.geocoding_service = GeocodingService()

    def search_places(
        self,
        city: str,
        category: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Search places in a city.
        """

        if not city.strip():
            raise ValueError("City cannot be empty.")

        if not category.strip():
            raise ValueError("Category cannot be empty.")

        if limit <= 0:
            raise ValueError("Limit must be greater than zero.")

        category = category.lower()

        if category not in self.CATEGORY_MAPPING:
            raise ValueError(
                f"Unsupported category: {category}"
            )

        location = self.geocoding_service.get_coordinates(city)

        latitude = location["latitude"]
        longitude = location["longitude"]

        params = {
            "categories": self.CATEGORY_MAPPING[category],
            "filter": f"circle:{longitude},{latitude},5000",
            "limit": limit,
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

                from app.schemas.api.response_models import PlacesResponseModel
                validated = PlacesResponseModel.model_validate(data)

                places = []

                for place in validated.features:

                    properties = place.properties

                    places.append(
                        {
                            "name": properties.name,
                            "address": properties.formatted,
                            "latitude": properties.lat,
                            "longitude": properties.lon,
                            "categories": properties.categories,
                        }
                    )

                logger.info(
                    f"Found {len(places)} {category}(s) in {city}"
                )

                return places

        except httpx.HTTPStatusError as error:

            logger.error(
                f"Geoapify API Error: {error.response.text}"
            )

            raise Exception(
                f"Unable to search {category} in {city}."
            ) from error

        except httpx.RequestError as error:

            logger.error(error)

            raise Exception(
                "Unable to connect to Geoapify."
            ) from error

        except Exception as error:

            logger.exception(error)

            raise