from loguru import logger
from langchain_core.tools import tool
from app.services.maps_service import MapsService

_maps_service = MapsService()


@tool
def get_route(origin: str, destination: str, mode: str = "drive") -> dict:
    """Get driving or transit route and distance between two locations."""
    logger.info(f"Maps Tool invoked (origin='{origin}', destination='{destination}', mode='{mode}')")
    return _maps_service.get_route(
        origin=origin,
        destination=destination,
        mode=mode,
    )


class MapsTool:
    def get_route(self, origin: str, destination: str, mode: str = "drive") -> dict:
        return get_route.invoke({
            "origin": origin,
            "destination": destination,
            "mode": mode,
        })