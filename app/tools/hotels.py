from loguru import logger

from app.services.places_service import PlacesService


class HotelTool:
    """
    Tool responsible for searching hotels.
    """

    def __init__(self):
        self.places_service = PlacesService()

    def search_hotels(
        self,
        city: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Search hotels in a city.

        Args:
            city: City name.
            limit: Maximum number of hotels.

        Returns:
            List of hotels.
        """

        logger.info(
            f"Hotel Tool invoked for city='{city}', limit={limit}"
        )

        return self.places_service.search_places(
            city=city,
            category="hotel",
            limit=limit,
        )