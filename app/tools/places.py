from loguru import logger
from langchain_core.tools import tool
from app.services.places_service import PlacesService

_places_service = PlacesService()


@tool
def search_places(city: str, category: str = "tourism.sights", limit: int = 5) -> list[dict]:
    """Search tourist attractions, places of interest, and monuments in a city."""
    logger.info(f"Places Tool invoked for city='{city}', category='{category}', limit={limit}")
    return _places_service.search_places(
        city=city,
        category=category,
        limit=limit,
    )


class PlacesTool:
    def search_places(self, city: str, category: str = "tourism.sights", limit: int = 5) -> list[dict]:
        return search_places.invoke({
            "city": city,
            "category": category,
            "limit": limit,
        })