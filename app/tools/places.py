from loguru import logger
from langchain_core.tools import tool
from app.services.places_service import PlacesService
from app.schemas.tool_result import ToolResult

_places_service = PlacesService()


@tool
def search_places(city: str, category: str = "tourism.sights", limit: int = 5) -> ToolResult:
    """Search tourist attractions, places of interest, and monuments in a city."""
    logger.info(f"Places Tool invoked for city='{city}', category='{category}', limit={limit}")
    try:
        data = _places_service.search_places(
            city=city,
            category=category,
            limit=limit,
        )
        return ToolResult(success=True, data=data)
    except Exception as e:
        logger.warning(f"Places Tool failed: {e}")
        return ToolResult(success=False, error=str(e), data=[])


class PlacesTool:
    def search_places(self, city: str, category: str = "tourism.sights", limit: int = 5) -> ToolResult:
        return search_places.invoke({
            "city": city,
            "category": category,
            "limit": limit,
        })