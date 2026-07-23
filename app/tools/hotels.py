from loguru import logger
from langchain_core.tools import tool
from app.services.places_service import PlacesService

_places_service = PlacesService()


@tool
def search_hotels(city: str, limit: int = 5) -> list[dict]:
    """Search accommodations and hotels in a city."""
    logger.info(f"Hotel Tool invoked for city='{city}', limit={limit}")
    return _places_service.search_places(
        city=city,
        category="hotel",
        limit=limit,
    )


class HotelTool:
    def search_hotels(self, city: str, limit: int = 5) -> list[dict]:
        return search_hotels.invoke({
            "city": city,
            "limit": limit,
        })