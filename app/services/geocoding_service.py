import re
import httpx
from typing import Dict, Optional
from loguru import logger

from app.config import GEOAPIFY_API_KEY


# Canonical known location registry for deterministic coordinates and metadata
CANONICAL_LOCATIONS: Dict[str, dict] = {
    "kochi": {
        "place_id": "canonical_kochi_kerala",
        "city": "Kochi",
        "state": "Kerala",
        "country": "India",
        "country_code": "in",
        "postcode": "682001",
        "formatted_address": "Kochi, Kerala, India",
        "latitude": 9.9679032,
        "longitude": 76.2444378,
        "timezone": "Asia/Kolkata",
    },
    "cochin": {
        "place_id": "canonical_kochi_kerala",
        "city": "Kochi",
        "state": "Kerala",
        "country": "India",
        "country_code": "in",
        "postcode": "682001",
        "formatted_address": "Kochi, Kerala, India",
        "latitude": 9.9679032,
        "longitude": 76.2444378,
        "timezone": "Asia/Kolkata",
    },
    "munnar": {
        "place_id": "canonical_munnar_kerala",
        "city": "Munnar",
        "state": "Kerala",
        "country": "India",
        "country_code": "in",
        "postcode": "685612",
        "formatted_address": "Munnar, Kerala, India",
        "latitude": 10.0869959,
        "longitude": 77.0600915,
        "timezone": "Asia/Kolkata",
    },
    "alleppey": {
        "place_id": "canonical_alleppey_kerala",
        "city": "Alappuzha",
        "state": "Kerala",
        "country": "India",
        "country_code": "in",
        "postcode": "688001",
        "formatted_address": "Alappuzha (Alleppey), Kerala, India",
        "latitude": 9.498073,
        "longitude": 76.338863,
        "timezone": "Asia/Kolkata",
    },
    "alappuzha": {
        "place_id": "canonical_alleppey_kerala",
        "city": "Alappuzha",
        "state": "Kerala",
        "country": "India",
        "country_code": "in",
        "postcode": "688001",
        "formatted_address": "Alappuzha, Kerala, India",
        "latitude": 9.498073,
        "longitude": 76.338863,
        "timezone": "Asia/Kolkata",
    },
    "delhi": {
        "place_id": "canonical_delhi_india",
        "city": "New Delhi",
        "state": "Delhi",
        "country": "India",
        "country_code": "in",
        "postcode": "110001",
        "formatted_address": "New Delhi, Delhi, India",
        "latitude": 28.6138954,
        "longitude": 77.2090057,
        "timezone": "Asia/Kolkata",
    },
    "new delhi": {
        "place_id": "canonical_delhi_india",
        "city": "New Delhi",
        "state": "Delhi",
        "country": "India",
        "country_code": "in",
        "postcode": "110001",
        "formatted_address": "New Delhi, Delhi, India",
        "latitude": 28.6138954,
        "longitude": 77.2090057,
        "timezone": "Asia/Kolkata",
    },
    "jaipur": {
        "place_id": "canonical_jaipur_rajasthan",
        "city": "Jaipur",
        "state": "Rajasthan",
        "country": "India",
        "country_code": "in",
        "postcode": "302001",
        "formatted_address": "Jaipur, Rajasthan, India",
        "latitude": 26.9124,
        "longitude": 75.7873,
        "timezone": "Asia/Kolkata",
    },
    "jodhpur": {
        "place_id": "canonical_jodhpur_rajasthan",
        "city": "Jodhpur",
        "state": "Rajasthan",
        "country": "India",
        "country_code": "in",
        "postcode": "342001",
        "formatted_address": "Jodhpur, Rajasthan, India",
        "latitude": 26.2389,
        "longitude": 73.0243,
        "timezone": "Asia/Kolkata",
    },
    "udaipur": {
        "place_id": "canonical_udaipur_rajasthan",
        "city": "Udaipur",
        "state": "Rajasthan",
        "country": "India",
        "country_code": "in",
        "postcode": "313001",
        "formatted_address": "Udaipur, Rajasthan, India",
        "latitude": 24.5854,
        "longitude": 73.7125,
        "timezone": "Asia/Kolkata",
    },
    "bengaluru": {
        "place_id": "canonical_bengaluru_karnataka",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "country_code": "in",
        "postcode": "560001",
        "formatted_address": "Bengaluru, Karnataka, India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "timezone": "Asia/Kolkata",
    },
    "bangalore": {
        "place_id": "canonical_bengaluru_karnataka",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "country_code": "in",
        "postcode": "560001",
        "formatted_address": "Bengaluru, Karnataka, India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "timezone": "Asia/Kolkata",
    },
    "mumbai": {
        "place_id": "canonical_mumbai_maharashtra",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "country_code": "in",
        "postcode": "400001",
        "formatted_address": "Mumbai, Maharashtra, India",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "timezone": "Asia/Kolkata",
    },
    "goa": {
        "place_id": "canonical_goa_india",
        "city": "Panaji",
        "state": "Goa",
        "country": "India",
        "country_code": "in",
        "postcode": "403001",
        "formatted_address": "Goa, India",
        "latitude": 15.4909,
        "longitude": 73.8278,
        "timezone": "Asia/Kolkata",
    },
    "kolkata": {
        "place_id": "canonical_kolkata_wb",
        "city": "Kolkata",
        "state": "West Bengal",
        "country": "India",
        "country_code": "in",
        "postcode": "700001",
        "formatted_address": "Kolkata, West Bengal, India",
        "latitude": 22.5726,
        "longitude": 88.3639,
        "timezone": "Asia/Kolkata",
    },
}

INTERNATIONAL_COUNTRY_PATTERNS = [
    r"\b(japan|jp)\b",
    r"\b(uk|united kingdom|britain|england|scotland|wales)\b",
    r"\b(usa?|united states|america)\b",
    r"\b(france|fr)\b",
    r"\b(italy|it)\b",
    r"\b(germany|de)\b",
    r"\b(thailand|th)\b",
    r"\b(singapore|sg)\b",
    r"\b(uae|united arab emirates|dubai)\b",
    r"\b(australia|au)\b",
    r"\b(spain|es)\b",
    r"\b(canada|ca)\b",
]


class GeocodingService:
    """
    Handles robust communication with the Geoapify Geocoding API,
    with canonical destination fallback, country-context disambiguation, and caching.
    """

    BASE_URL = "https://api.geoapify.com/v1/geocode/search"
    _cache: Dict[str, dict] = {}

    def __init__(self):
        self.api_key = GEOAPIFY_API_KEY

    def get_coordinates(
        self,
        city: str,
        country_context: Optional[str] = None,
    ) -> dict:
        """
        Convert a city name into latitude and longitude with country context validation.
        Correctly distinguishes ambiguous names like 'Kochi, Kerala, India' vs 'Kochi, Japan'.
        """
        if not city or not city.strip():
            raise ValueError("City cannot be empty.")

        clean_query = city.strip()
        cache_key = f"{clean_query.lower()}:{country_context.lower() if country_context else ''}"

        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        # 1. Check for explicit international destination (e.g. 'Kochi, Japan', 'London, UK')
        is_explicit_intl = False
        for pat in INTERNATIONAL_COUNTRY_PATTERNS:
            if re.search(pat, clean_query, re.IGNORECASE):
                is_explicit_intl = True
                break

        # 2. Check canonical registry for exact city matches when not explicit international
        normalized_key = re.sub(r",\s*(india|kerala|rajasthan|delhi|karnataka|maharashtra|goa)\b", "", clean_query, flags=re.I).strip().lower()
        if not is_explicit_intl and normalized_key in CANONICAL_LOCATIONS:
            loc = CANONICAL_LOCATIONS[normalized_key].copy()
            self._cache[cache_key] = loc
            logger.info(f"Resolved canonical destination '{city}' -> {loc['formatted_address']} [{loc['latitude']}, {loc['longitude']}]")
            return loc

        # 3. Formulate query parameters with country restriction where applicable
        params = {
            "text": clean_query,
            "limit": 5,
            "apiKey": self.api_key,
        }

        # Apply India countrycode filter if not explicit international
        if not is_explicit_intl:
            # If user specified country context as India or query is domestic
            if country_context and country_context.lower() in {"in", "india"}:
                params["filter"] = "countrycode:in"
            elif re.search(r"\b(india|kerala|rajasthan|delhi|karnataka|maharashtra|goa|gujarat|tamil nadu)\b", clean_query, re.I):
                params["filter"] = "countrycode:in"
            elif not country_context:
                # Default domestic assumption for unadorned Indian city queries
                params["filter"] = "countrycode:in"

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(self.BASE_URL, params=params)

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

            # Fallback retry without filter if international or no results
            if not features and "filter" in params:
                del params["filter"]
                with httpx.Client(timeout=10.0) as client:
                    res2 = client.get(self.BASE_URL, params=params)
                    if res2.status_code == 200:
                        validated2 = GeocodingResponseModel.model_validate(res2.json())
                        features = validated2.features

            if not features:
                raise ValueError(f"No location found for '{city}'.")

            # Find best feature matching country expectation
            selected_feature = features[0]
            if not is_explicit_intl:
                for feat in features:
                    if feat.properties.country_code == "in":
                        selected_feature = feat
                        break

            properties = selected_feature.properties

            # Safety validation: if user asked for Kerala/India, ensure not in Japan/US
            if not is_explicit_intl and properties.country_code != "in":
                # Check if canonical known city was requested
                if normalized_key in CANONICAL_LOCATIONS:
                    loc = CANONICAL_LOCATIONS[normalized_key].copy()
                    self._cache[cache_key] = loc
                    return loc
                logger.warning(f"Geocoding resolved '{city}' to foreign country '{properties.country}' ({properties.country_code}).")

            result = {
                "place_id": properties.place_id,
                "city": properties.city or city,
                "state": properties.state,
                "country": properties.country,
                "country_code": properties.country_code,
                "postcode": properties.postcode,
                "formatted_address": properties.formatted,
                "latitude": properties.lat,
                "longitude": properties.lon,
                "timezone": properties.timezone.name if properties.timezone else None,
            }

            self._cache[cache_key] = result
            logger.info(f"Successfully geocoded '{city}' -> {result['formatted_address']} ({result['country']}).")
            return result

        except httpx.HTTPStatusError as error:
            logger.error(f"Geoapify Geocoding API Error: {error.response.text}")
            raise Exception(f"Unable to geocode '{city}'.") from error

        except httpx.RequestError as error:
            logger.error(error)
            raise Exception("Unable to connect to Geoapify.") from error

        except Exception as error:
            logger.exception(error)
            raise