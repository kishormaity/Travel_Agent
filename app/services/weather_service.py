import httpx
from loguru import logger

from app.config import (
    WEATHER_API_KEY,
    WEATHER_API_BASE_URL,
)


class WeatherService:
    """
    Handles all communication with the WeatherAPI service.
    """

    def __init__(self):
        self.api_key = WEATHER_API_KEY
        self.base_url = WEATHER_API_BASE_URL

    def get_current_weather(self, city: str) -> dict:
        """
        Fetch the current weather for a given city.
        """

        endpoint = f"{self.base_url}/current.json"

        params = {
            "key": self.api_key,
            "q": city,
            "aqi": "no",
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    endpoint,
                    params=params,
                )

                response.raise_for_status()

                data = response.json()

                logger.info(
                    f"Successfully fetched weather for city='{city}'"
                )

                return {
                    "city": data["location"]["name"],
                    "region": data["location"]["region"],
                    "country": data["location"]["country"],
                    "latitude": data["location"]["lat"],
                    "longitude": data["location"]["lon"],
                    "local_time": data["location"]["localtime"],
                    "temperature_c": data["current"]["temp_c"],
                    "temperature_f": data["current"]["temp_f"],
                    "condition": data["current"]["condition"]["text"],
                    "humidity": data["current"]["humidity"],
                    "wind_kph": data["current"]["wind_kph"],
                    "wind_direction": data["current"]["wind_dir"],
                    "feels_like_c": data["current"]["feelslike_c"],
                    "visibility_km": data["current"]["vis_km"],
                    "uv_index": data["current"]["uv"],
                }

        except httpx.HTTPStatusError as error:
            logger.error(
                f"Weather API returned an error for city='{city}': "
                f"{error.response.text}"
            )

            raise Exception(
                f"Weather API error while fetching weather for '{city}'."
            ) from error

        except httpx.RequestError as error:
            logger.error(
                f"Failed to connect to Weather API: {error}"
            )

            raise Exception(
                "Unable to connect to the Weather API."
            ) from error

        except Exception as error:
            logger.exception(
                f"Unexpected error while fetching weather for '{city}'"
            )

            raise