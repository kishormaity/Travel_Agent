"""
Remote Hosted MCP Tool Permissions and Human-in-the-Loop Guardrails.
"""

from typing import Set, Dict

# Strict mapping of agents to allowed remote MCP tool names
REMOTE_AGENT_TOOL_PERMISSIONS: Dict[str, Set[str]] = {
    "flight_agent": {
        "flight_octotrip_search",
        "octotrip_search",
        "fli_search_flights",
        "fli_search_dates",
        "fli_get_booking_options",
        "fli_find_airports",
        "search_flights",
        "search_dates",
    },
    "accommodation_agent": {
        "maqami_get_data_hotels",
        "maqami_get_data_hotel_search",
        "maqami_get_data_hotel",
        "maqami_get_data_reviews",
        "maqami_get_data_facilities",
        "maqami_get_data_hotels_semantic_search",
        "maqami_get_data_hotel_ask",
        "maqami_get_data_cities",
        "maqami_get_data_countries",
        # OBO Travel MCP Tools (Sole Accommodation MCP Provider)
        "obo_search_destinations",
        "obo_resolve_destination",
        "obo_search_hotels",
        "obo_get_hotel_details",
        "obo_get_hotel_offers",
        "obo_get_offer_policies",
        "obo_get_price_calendar",
        "obo_find_deals",
        "obo_plan_trips",
        "obo_get_trip_ideas",
        "obo_compare_hotels",
        "obo_search_flexible_dates",
        "obo_find_cheapest_weekends",
        "obo_create_booking_link",
        # HasData MCP Tools (Google Hotels)
        "hasdata_google_travel_hotels_getGoogleHotels",
        "hasdata_hasdata_google_travel_hotels_getGoogleHotels",
    },
    "destination_agent": {
        "ticketlens_search_experiences",
        "ticketlens_search_tours",
        "ticketlens_get_tour",
        "ticketlens_search_pois",
        "ticketlens_get_poi",
        "ticketlens_health_check",
        # HasData MCP Tools (Google Maps Places & Reviews)
        "hasdata_google_maps_search_getSearchResults",
        "hasdata_google_maps_place_getPlaceDetails",
        "hasdata_google_maps_reviews_getPlaceReviews",
        "hasdata_hasdata_google_maps_search_performMapSearch",
        "hasdata_hasdata_google_maps_place_getPlaceDetails",
        "hasdata_hasdata_google_maps_reviews_getMapReviews",
    },
}

# Sensitive / irreversible operations requiring explicit Human-in-the-Loop confirmation
SENSITIVE_IRREVERSIBLE_TOOLS: Set[str] = {
    "maqami_post_rates_prebook",
    "maqami_cancel_hotel_booking",
    "maqami_cancelExperienceBooking",
    "maqami_put_bookings_bookingid_amend",
    "maqami_post_bookings_bookingid_alternative_prebooks",
}


def is_remote_tool_permitted(agent_name: str, tool_name: str) -> bool:
    """Verifies if an agent is authorized to invoke a specific remote MCP tool."""
    allowed = REMOTE_AGENT_TOOL_PERMISSIONS.get(agent_name, set())
    if tool_name in allowed:
        return True
    if agent_name == "flight_agent" and ("octotrip" in tool_name.lower() or "fli" in tool_name.lower()):
        return True
    if agent_name == "accommodation_agent" and tool_name.startswith("obo_"):
        return True
    return False


def requires_human_confirmation(tool_name: str) -> bool:
    """Checks if a tool performs an irreversible action (booking, cancellation, payment)."""
    return tool_name in SENSITIVE_IRREVERSIBLE_TOOLS
