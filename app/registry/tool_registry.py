from langchain_core.tools import render_text_description

from app.tools.weather import get_current_weather
from app.tools.currency import convert_currency
from app.tools.places import search_places
from app.tools.flights import search_flights
from app.tools.hotels import search_hotels
from app.tools.maps import get_route


LANGCHAIN_TOOLS = [
    get_current_weather,
    convert_currency,
    search_places,
    search_flights,
    search_hotels,
    get_route,
]


AVAILABLE_TOOLS = {tool.name: tool for tool in LANGCHAIN_TOOLS}
AVAILABLE_TOOLS["llm_reasoning"] = None


def get_planner_tools_description() -> str:
    """
    Generate a formatted tool description for the Planner Agent using LangChain's render_text_description.
    """
    return render_text_description(LANGCHAIN_TOOLS)