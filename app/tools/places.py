from loguru import logger

from app.services.places_service import PlacesService


class PlacesTool:
    """
    Tool responsible for searching places.
    """

    def __init__(self):
        self.places_service = PlacesService()

    def search_places(
        self,
        city: str,
        category: str,
        limit: int = 5,
    ) -> list[dict]:
        """
        Search for places in a city.

        Args:
            city: Name of the city.
            category: Type of place to search.
            limit: Maximum number of results.

        Returns:
            List of places.
        """

        logger.info(
            f"Places Tool invoked for city='{city}', "
            f"category='{category}', limit={limit}"
        )

        return self.places_service.search_places(
            city=city,
            category=category,
            limit=limit,
        )