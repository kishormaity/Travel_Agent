from loguru import logger

from app.services.weather_service import WeatherService


class WeatherTool:
    """
    Tool responsible for fetching the current weather.
    """

    def __init__(self):
        self.weather_service = WeatherService()

    def get_current_weather(self, city: str) -> dict:
        """
        Fetch the current weather for a given city.
        """

        logger.info(
            f"Weather Tool invoked for city='{city}'"
        )

        weather = self.weather_service.get_current_weather(city)

        return weather