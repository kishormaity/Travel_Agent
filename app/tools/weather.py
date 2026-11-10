from typing import Optional
from loguru import logger
from langchain_core.tools import tool
from app.services.weather_service import WeatherService
from app.schemas.tool_result import ToolResult
from app.core.cache import weather_cache

_weather_service = WeatherService()


def normalize_weather_city(city: str) -> str:
    """Normalizes city names for weather tool, stripping country and fixing typos."""
    if not city:
        return ""
    clean = str(city).strip()
    # Strip country/state if present (e.g., 'Jodhpur, Rajasthan' -> 'Jodhpur')
    if "," in clean:
        clean = clean.split(",")[0].strip()

    clean_lower = clean.lower()
    typos = {
        "jodhur": "Jodhpur",
        "jodhpu": "Jodhpur",
        "jodpur": "Jodhpur",
        "jaipue": "Jaipur",
        "jaipr": "Jaipur",
        "udipur": "Udaipur",
        "udaipr": "Udaipur",
        "kolkatta": "Kolkata",
        "banglore": "Bengaluru",
        "bengalor": "Bengaluru",
        "mumbay": "Mumbai",
        "delhy": "Delhi",
    }
    if clean_lower in typos:
        logger.info(f"[WeatherTool] Corrected city typo '{city}' -> '{typos[clean_lower]}'")
        return typos[clean_lower]
    return clean.title() if len(clean) > 3 else clean


@tool
def get_current_weather(
    city: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days: Optional[int] = None,
) -> ToolResult:
    """Get day-by-day weather forecasts for a destination city across the requested travel dates (start_date to end_date). Returns day-wise temperatures (high/low), weather conditions, rain chance, and sightseeing recommendations for each day of the journey."""
    logger.info(f"Weather Tool invoked for city='{city}', start_date='{start_date}', end_date='{end_date}', days={days}")
    if not city or not str(city).strip():
        return ToolResult(success=False, error="City name cannot be empty.", data={})

    norm_city = normalize_weather_city(city)
    cache_key = f"{norm_city.lower()}_{start_date}_{end_date}_{days}"
    cached_data = weather_cache.get(cache_key)
    if cached_data is not None:
        logger.info(f"[WeatherTool] Cache HIT for key='{cache_key}' (sub-millisecond return)")
        return ToolResult(success=True, data=cached_data)

    try:
        data = _weather_service.get_weather_forecast(
            city=norm_city,
            start_date=start_date,
            end_date=end_date,
            days=days,
        )
        if data:
            weather_cache.set(cache_key, data)
        return ToolResult(success=True, data=data)
    except Exception as e:
        logger.warning(f"[WeatherTool] Error fetching weather for '{city}' (normalized: '{norm_city}'): {e}")
        return ToolResult(success=False, error=str(e), data={})


class WeatherTool:
    def get_current_weather(
        self,
        city: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None,
    ) -> ToolResult:
        return get_current_weather.invoke({
            "city": city,
            "start_date": start_date,
            "end_date": end_date,
            "days": days,
        })
