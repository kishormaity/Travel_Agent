from loguru import logger
from langchain_core.tools import tool
from app.services.weather_service import WeatherService

_weather_service = WeatherService()


@tool
def get_current_weather(city: str) -> dict:
    """Get the current weather information for a given city."""
    logger.info(f"Weather Tool invoked for city='{city}'")
    return _weather_service.get_current_weather(city)


class WeatherTool:
    def get_current_weather(self, city: str) -> dict:
        return get_current_weather.invoke({"city": city})