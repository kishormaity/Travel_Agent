from typing import Optional
from loguru import logger
from langchain_core.tools import tool
from app.core.config import settings
from app.services.places_service import PlacesService
from app.schemas.tool_result import ToolResult
from app.mcp.remote import remote_mcp_manager
from app.core.cache import hotels_cache

_places_service = PlacesService()


@tool
def search_hotels(
    city: str,
    check_in_date: Optional[str] = None,
    check_out_date: Optional[str] = None,
    adults: int = 2,
    rooms: Optional[int] = None,
    limit: Optional[int] = None,
) -> ToolResult:
    """Search accommodations and hotels in a city for specified dates and traveler group. Returns all available hotels by default."""
    logger.info(
        f"Hotel Tool invoked for city='{city}', check_in={check_in_date}, "
        f"check_out={check_out_date}, adults={adults}, rooms={rooms}, limit={limit}"
    )
    if not city or not str(city).strip():
        return ToolResult(success=False, error="City name cannot be empty.", data=[])

    cache_key = f"{str(city).strip().lower()}_{check_in_date}_{check_out_date}_{adults}_{rooms}_{limit}"
    cached = hotels_cache.get(cache_key)
    if cached is not None:
        logger.info(f"[HotelTool] Cache HIT for key='{cache_key}' (sub-millisecond return)")
        return cached

    # 1. Primary: Attempt HasData Google Hotels search if API key and dates are provided
    if settings.hasdata_api_key and check_in_date and check_out_date:
        from app.agents.accommodation.normalizer import normalize_hasdata_hotel_results
        try:
            query_city = f"{city}, India" if "india" not in city.lower() else city
            logger.info(f"Querying HasData Google Hotels (primary) for '{query_city}'...")
            mcp_res = remote_mcp_manager.execute_tool(
                agent_name="accommodation_agent",
                tool_name="hasdata_google_travel_hotels_getGoogleHotels",
                arguments={
                    "q": query_city,
                    "checkInDate": str(check_in_date).strip(),
                    "checkOutDate": str(check_out_date).strip(),
                    "adults": int(adults),
                    "currency": "INR",
                },
            )
            if mcp_res.get("success") and mcp_res.get("data"):
                normalized = normalize_hasdata_hotel_results(
                    raw_response=mcp_res["data"],
                    city=city,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                    adults=adults,
                    rooms=rooms,
                    currency="INR",
                    limit=limit,
                )
                if normalized:
                    logger.info(f"Successfully retrieved {len(normalized)} hotels from HasData Google Hotels.")
                    res = ToolResult(success=True, data=normalized)
                    hotels_cache.set(cache_key, res)
                    return res
            else:
                err = mcp_res.get("error", "No data returned")
                logger.warning(f"HasData Google Hotels returned unsuccessful ({err}). Falling back to Geoapify.")
        except Exception as exc:
            logger.warning(f"HasData Google Hotels execution failed: {exc}. Gracefully falling back to Geoapify Places.")

    # 2. Fallback: Geoapify Places
    geo_limit = limit if limit is not None else 50
    logger.info(f"Using Geoapify Places for hotel discovery in '{city}' (fallback/default, limit={geo_limit}).")
    data = _places_service.search_places(
        city=city,
        category="hotel",
        limit=geo_limit,
        check_in_date=check_in_date,
        check_out_date=check_out_date,
        adults=adults,
        rooms=rooms,
    )
    fallback_res = ToolResult(success=True, data=data)
    if data:
        hotels_cache.set(cache_key, fallback_res)
    return fallback_res



class HotelTool:
    def search_hotels(
        self,
        city: str,
        check_in_date: Optional[str] = None,
        check_out_date: Optional[str] = None,
        adults: int = 2,
        rooms: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> ToolResult:
        return search_hotels.invoke({
            "city": city,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "adults": adults,
            "rooms": rooms,
            "limit": limit,
        })