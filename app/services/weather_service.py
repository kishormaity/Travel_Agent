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

                if response.status_code != 200:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get("error", {}).get("message")
                        if error_msg:
                            raise Exception(f"Weather API error message: {error_msg}")
                    except Exception as e:
                        if "Weather API error message" in str(e):
                            raise e

                response.raise_for_status()
                data = response.json()

                from app.schemas.api.response_models import WeatherResponseModel
                validated = WeatherResponseModel.model_validate(data)

                logger.info(
                    f"Successfully fetched weather for city='{city}'"
                )

                return {
                    "city": validated.location.name,
                    "region": validated.location.region,
                    "country": validated.location.country,
                    "latitude": validated.location.lat,
                    "longitude": validated.location.lon,
                    "local_time": validated.location.localtime,
                    "temperature_c": validated.current.temp_c,
                    "temperature_f": validated.current.temp_f,
                    "condition": validated.current.condition.text,
                    "humidity": validated.current.humidity,
                    "wind_kph": validated.current.wind_kph,
                    "wind_direction": validated.current.wind_dir,
                    "feels_like_c": validated.current.feelslike_c,
                    "visibility_km": validated.current.vis_km,
                    "uv_index": validated.current.uv,
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