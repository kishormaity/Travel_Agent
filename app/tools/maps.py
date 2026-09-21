from loguru import logger
from langchain_core.tools import tool
from app.services.maps_service import MapsService
from app.schemas.tool_result import ToolResult

_maps_service = MapsService()


@tool
def get_route(origin: str, destination: str, mode: str = "drive") -> ToolResult:
    """Get driving or transit route and distance between two locations."""
    logger.info(f"Maps Tool invoked (origin='{origin}', destination='{destination}', mode='{mode}')")
    if not origin or not str(origin).strip() or not destination or not str(destination).strip():
        return ToolResult(success=False, error="Origin and destination cannot be empty.", data={})
    data = _maps_service.get_route(
        origin=origin,
        destination=destination,
        mode=mode,
    )
    return ToolResult(success=True, data=data)



class MapsTool:
    def get_route(self, origin: str, destination: str, mode: str = "drive") -> ToolResult:
        return get_route.invoke({
            "origin": origin,
            "destination": destination,
            "mode": mode,
        })