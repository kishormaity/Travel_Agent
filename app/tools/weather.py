from loguru import logger
from langchain_core.tools import tool
from app.services.weather_service import WeatherService
from app.schemas.tool_result import ToolResult

_weather_service = WeatherService()


@tool
def get_current_weather(city: str) -> ToolResult:
    """Get the current weather information for a given city."""
    logger.info(f"Weather Tool invoked for city='{city}'")
    if not city or not str(city).strip():
        return ToolResult(success=False, error="City name cannot be empty.", data={})
    data = _weather_service.get_current_weather(city)
    return ToolResult(success=True, data=data)


class WeatherTool:
    def get_current_weather(self, city: str) -> ToolResult:
        return get_current_weather.invoke({"city": city})