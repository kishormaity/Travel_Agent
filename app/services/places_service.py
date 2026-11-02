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
        "restaurants": "catering.restaurant",
        "cafe": "catering.cafe",
        "hotel": "accommodation.hotel",
        "hotels": "accommodation.hotel",
        "accommodation": "accommodation.hotel",
        "resort": "accommodation.hotel",
        "resorts": "accommodation.hotel",
        "airport": "airport",
        "hospital": "healthcare.hospital",
        "atm": "service.financial.atm",
        "museum": "entertainment.museum",
        "museums": "entertainment.museum",
        "tourist_attraction": "tourism.attraction",
        "tourism.attraction": "tourism.attraction",
        "tourism.sights": "tourism.attraction",
        "sights": "tourism.attraction",
        "attraction": "tourism.attraction",
        "attractions": "tourism.attraction",
        "sightseeing": "tourism.attraction",
        "places": "tourism.attraction",
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
        category: str = "tourism.attraction",
        limit: int = 5,
        check_in_date: str = None,
        check_out_date: str = None,
        adults: int = 2,
        rooms: int = None,
    ) -> list[dict]:
        """
        Search places or hotels in a city with resilient category mapping,
        country-aware geocoding, and enriched accommodation metadata.
        """
        if not city or not city.strip():
            logger.warning("Empty city name provided to search_places.")
            return []

        cat_key = (category or "tourism.attraction").lower().strip()
        is_hotel_query = cat_key in {"hotel", "hotels", "accommodation", "resort", "resorts"}
        mapped_category = self.CATEGORY_MAPPING.get(cat_key, "accommodation.hotel" if is_hotel_query else "tourism.attraction")

        try:
            location = self.geocoding_service.get_coordinates(city)
            latitude = location["latitude"]
            longitude = location["longitude"]

            params = {
                "categories": mapped_category,
                "filter": f"circle:{longitude},{latitude},15000",
                "limit": max(1, limit),
                "apiKey": self.api_key,
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()
                from app.schemas.api.response_models import PlacesResponseModel
                validated = PlacesResponseModel.model_validate(data)

                places = []
                for place in validated.features:
                    properties = place.properties
                    prop_name = properties.name or (f"Accommodation in {city}" if is_hotel_query else f"Attraction in {city}")
                    
                    if is_hotel_query:
                        rec_rooms = rooms if rooms else (1 if adults <= 2 else (2 if adults <= 4 else max(1, adults // 2)))
                        places.append(
                            {
                                "property_name": prop_name,
                                "name": prop_name,
                                "address": properties.formatted,
                                "city": location.get("city", city),
                                "state": location.get("state"),
                                "country": location.get("country"),
                                "latitude": properties.lat,
                                "longitude": properties.lon,
                                "categories": properties.categories,
                                "data_source": "geoapify_places",
                                "live_rates_available": False,
                                "pricing_notice": "Live dynamic room rates not provided by metadata discovery; verify on direct booking sites.",
                                "check_in_date": check_in_date,
                                "check_out_date": check_out_date,
                                "adults": adults,
                                "recommended_rooms": rec_rooms,
                                "room_guidance": f"For {adults} adult(s), {rec_rooms} room(s) is typical. Do not assume {adults} separate rooms are needed.",
                            }
                        )
                    else:
                        places.append(
                            {
                                "name": prop_name,
                                "address": properties.formatted,
                                "latitude": properties.lat,
                                "longitude": properties.lon,
                                "categories": properties.categories,
                            }
                        )

                logger.info(f"Found {len(places)} {cat_key}(s) in {city}")
                return places

        except (httpx.HTTPStatusError, httpx.RequestError) as error:
            logger.error(f"Geoapify Places API network/HTTP error for city '{city}': {error}")
            raise
        except ValueError as val_err:
            logger.warning(f"Location resolution failed for '{city}': {val_err}")
            return []