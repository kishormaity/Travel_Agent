from loguru import logger
from langchain_core.tools import tool
from app.services.places_service import PlacesService
from app.schemas.tool_result import ToolResult

_places_service = PlacesService()


@tool
def search_hotels(city: str, limit: int = 5) -> ToolResult:
    """Search accommodations and hotels in a city."""
    logger.info(f"Hotel Tool invoked for city='{city}', limit={limit}")
    try:
        data = _places_service.search_places(
            city=city,
            category="hotel",
            limit=limit,
        )
        return ToolResult(success=True, data=data)
    except Exception as e:
        logger.warning(f"Hotel Tool failed: {e}")
        return ToolResult(success=False, error=str(e), data=[])


class HotelTool:
    def search_hotels(self, city: str, limit: int = 5) -> ToolResult:
        return search_hotels.invoke({
            "city": city,
            "limit": limit,
        })