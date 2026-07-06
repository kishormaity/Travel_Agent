from loguru import logger

from app.services.maps_service import MapsService


class MapsTool:
    """
    Tool responsible for route calculation.
    """

    def __init__(self):
        self.maps_service = MapsService()

    def get_route(
        self,
        origin: str,
        destination: str,
        mode: str = "drive",
    ) -> dict:
        """
        Get route between two locations.
        """

        logger.info(
            f"Maps Tool invoked "
            f"(origin='{origin}', "
            f"destination='{destination}', "
            f"mode='{mode}')"
        )

        return self.maps_service.get_route(
            origin=origin,
            destination=destination,
            mode=mode,
        )