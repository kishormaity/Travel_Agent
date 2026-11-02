import json
from datetime import datetime
from loguru import logger

from app.config import MODEL_NAME, RESPONSE_TEMPERATURE, MAX_TOKENS
from app.core import get_llm
from app.prompts import RESPONSE_SYSTEM_PROMPT
from app.schemas.planner import ExecutionPlan
from app.utils import summarize_result_with_llm


def format_flight_results_for_response(flights: list) -> dict:
    """Formats flight results preserving explicit outbound and return pairing without lossy compression."""
    if not flights or not isinstance(flights, list):
        return {"flights": []}

    formatted_options = []
    for f in flights[:5]:
        is_rt = f.get("is_round_trip", False)
        opt = {
            "flight_type": "COMPLETE ROUND-TRIP ITINERARY" if is_rt else "ONE-WAY FLIGHT ONLY (Return not included)",
            "airline": f.get("airline"),
            "total_price": f"{f.get('price')} {f.get('currency', 'INR')}",
            "baggage": f.get("baggage"),
            "booking_url": f.get("booking_url"),
            "outbound_journey": {
                "route": f"{f.get('origin')} -> {f.get('destination')}",
                "departure": f"{f.get('departure_date')} {f.get('departure_time')}",
                "arrival": f"{f.get('arrival_date')} {f.get('arrival_time')}",
                "flight_number": f.get("flight_number") or (f.get("flight_numbers", [""])[0] if f.get("flight_numbers") else None),
                "stops": f.get("stops", 0),
                "airline": f.get("outbound_airline") or f.get("airline"),
            }
        }
        if is_rt:
            opt["return_journey"] = {
                "route": f"{f.get('return_origin') or f.get('destination')} -> {f.get('return_destination') or f.get('origin')}",
                "departure": f"{f.get('return_departure_date')} {f.get('return_departure_time')}",
                "arrival": f"{f.get('return_arrival_date')} {f.get('return_arrival_time')}",
                "flight_number": (f.get("flight_numbers", ["", ""])[1] if len(f.get("flight_numbers", [])) > 1 else None),
                "stops": f.get("inbound_stops", 0),
                "airline": f.get("inbound_airline") or f.get("airline"),
            }
        formatted_options.append(opt)

    return {
        "itinerary_type": "Round-Trip" if any(f.get("is_round_trip") for f in flights) else "One-Way",
        "verified_flight_options": formatted_options
    }


def format_hotel_results_for_response(hotels: list) -> dict:
    """Formats hotel results preserving verified property names, addresses, live rates, ratings, and room guidance."""
    if not hotels or not isinstance(hotels, list):
        return {"accommodations": []}

    formatted = []
    has_any_live_rates = False
    for h in hotels[:5]:
        live_rates = h.get("live_rates_available", False)
        if live_rates:
            has_any_live_rates = True
        formatted.append({
            "property_name": h.get("property_name") or h.get("name"),
            "address": h.get("address"),
            "city": h.get("city"),
            "state": h.get("state"),
            "country": h.get("country"),
            "hotel_class": h.get("hotel_class"),
            "rating": h.get("rating"),
            "reviews": h.get("reviews"),
            "price_per_night": h.get("price_per_night_formatted") or h.get("price_per_night"),
            "total_price": h.get("total_price_formatted") or h.get("total_price"),
            "currency": h.get("currency", "INR"),
            "booking_url": h.get("booking_url"),
            "data_source": h.get("data_source", "places_service"),
            "live_rates_available": live_rates,
            "pricing_notice": h.get("pricing_notice", "Live room rates not provided; verify directly on booking sites."),
            "recommended_rooms": h.get("recommended_rooms"),
            "room_guidance": h.get("room_guidance"),
            "check_in_date": h.get("check_in_date"),
            "check_out_date": h.get("check_out_date"),
        })

    if has_any_live_rates:
        notice = "Live dynamic room rates and verified guest ratings retrieved via HasData Google Hotels."
    else:
        notice = (
            "Discovered verified properties via geographical places database. "
            "Live dynamic nightly pricing and real-time room availability require direct booking confirmation."
        )

    return {
        "verified_properties": formatted,
        "data_availability_notice": notice,
    }


def format_weather_results_for_response(weather_data: dict) -> dict:
    """Formats weather results to strictly separate real-time observations from seasonal climate."""
    if not weather_data or not isinstance(weather_data, dict):
        return {"weather": {}}

    return {
        "city": weather_data.get("city"),
        "region": weather_data.get("region"),
        "country": weather_data.get("country"),
        "temperature_c": weather_data.get("temperature_c"),
        "condition": weather_data.get("condition"),
        "humidity": weather_data.get("humidity"),
        "feels_like_c": weather_data.get("feels_like_c"),
        "observation_timestamp": weather_data.get("observation_time"),
        "source_provider": weather_data.get("provider", "WeatherAPI.com (real-time observation)"),
        "data_classification": (
            "REAL-TIME CURRENT OBSERVATION (Recorded at observation_timestamp). "
            "Not a forecast for future travel months. Specific future forecasts become available within 7-14 days of departure."
        ),
        "historical_climate_archive_available": False,
    }


import re

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # geometric shapes
    "\U0001F800-\U0001F8FF"  # supplemental arrows
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols & pictographs extended-a
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # enclosed alphanumeric / circled numbers
    "\U000020E3"              # keycap
    "\U0000FE0F"              # variation selector
    "]+",
    flags=re.UNICODE,
)


def clean_travel_report_formatting(text: str) -> str:
    """
    Sanitizes the generated response into clean, professional travel prose:
    1. Removes Markdown header hashes (##, ###, etc.) and numbered prefixes on headers
    2. Strips emojis and decorative icons
    3. Strips bold markers (**word**, __word__) and emphasis asterisks while preserving table pipes
    4. Removes blockquote markers ('>')
    5. Clean up excessive multiple colons (e.g. '::')
    6. Ensures proper spacing between sections
    """
    if not text:
        return ""

    # 1. Remove markdown heading hashes at the start of lines: e.g. '## 1. Flight Details' -> 'Flight Details'
    text = re.sub(r"^[ \t]*#{1,6}[ \t]*(?:[\d\.\)]+[ \t]+)?", "", text, flags=re.MULTILINE)

    # 2. Remove emojis and decorative icons
    text = EMOJI_PATTERN.sub("", text)

    # 3. Remove bold and italic markers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    # Remove remaining standalone emphasis asterisks
    text = re.sub(r"(?<=\w)\*(?=\w)", "", text)
    text = re.sub(r"(?<![\w|*])\*([^\*\n]+)\*(?![\w|*])", r"\1", text)

    # 4. Remove leading blockquote markers '>'
    text = re.sub(r"^[ \t]*>[ \t]*", "", text, flags=re.MULTILINE)

    # 5. Clean up excessive colons
    text = re.sub(r":{2,}", ":", text)

    # 6. Normalize whitespace and trailing spaces
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


class ResponseAgent:
    """Responsible for converting execution plan results into a natural language response."""

    def __init__(self):
        self.client = get_llm(max_tokens=4096)

    def generate_response(self, user_goal: str, execution_plan: ExecutionPlan) -> str:
        """Generate a user-friendly response based on tool execution results."""
        logger.info("Generating final response.")
        execution_summary = self._build_execution_summary(execution_plan)

        system_message = (
            f"{RESPONSE_SYSTEM_PROMPT}\n\n"
            f"Current Local Date and Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        user_content = f"User Request:\n{user_goal}\n\nExecution Results:\n{execution_summary}"

        from langchain_core.messages import SystemMessage, HumanMessage
        response = self.client.invoke([
            SystemMessage(content=system_message),
            HumanMessage(content=user_content),
        ])

        return clean_travel_report_formatting(response.content)

    def _build_execution_summary(self, execution_plan: ExecutionPlan) -> str:
        """Convert execution plan tasks into a compact JSON summary to minimize tokens while preserving critical flight pairing and accommodation transparency."""
        summary = []
        for task in execution_plan.tasks.values():
            if task.tool_name == "search_flights" and isinstance(task.result, list):
                res_val = format_flight_results_for_response(task.result)
            elif task.tool_name == "search_hotels" and isinstance(task.result, list):
                res_val = format_hotel_results_for_response(task.result)
            elif task.tool_name == "get_current_weather" and isinstance(task.result, dict):
                res_val = format_weather_results_for_response(task.result)
            else:
                res_val = summarize_result_with_llm(task.result)

            item = {
                "tool": task.tool_name,
                "description": task.description,
                "result": res_val,
            }
            if task.error:
                item["error"] = task.error
            summary.append(item)

        return json.dumps(summary, indent=2, default=str)