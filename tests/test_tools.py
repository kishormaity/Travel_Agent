import pytest
from unittest.mock import patch, MagicMock

from app.registry.tool_registry import AVAILABLE_TOOLS, LANGCHAIN_TOOLS, get_planner_tools_description
from app.registry.tool_executor import ToolExecutor
from app.schemas.tool_result import ToolResult
from app.tools.weather import get_current_weather
from app.tools.currency import convert_currency
from app.tools.hotels import search_hotels
from app.tools.flights import search_flights
from app.tools.maps import get_route
from app.tools.places import search_places


def test_tool_registry_contains_required_tools():
    expected = {
        "get_current_weather",
        "convert_currency",
        "search_places",
        "search_flights",
        "search_hotels",
        "get_route",
        "llm_reasoning",
    }
    assert expected.issubset(set(AVAILABLE_TOOLS.keys()))
    assert len(LANGCHAIN_TOOLS) == 6


def test_planner_tools_description_renders():
    desc = get_planner_tools_description()
    assert "get_current_weather" in desc
    assert "search_flights" in desc
    assert "search_hotels" in desc


def test_weather_tool_empty_city_handled_domain_response():
    result = get_current_weather.invoke({"city": ""})
    assert isinstance(result, ToolResult)
    assert result.success is False
    assert "cannot be empty" in result.error


def test_weather_tool_mocked_success():
    mock_weather_data = {
        "city": "Bengaluru",
        "temperature_c": 27.0,
        "condition": "Partly cloudy",
    }
    with patch("app.tools.weather._weather_service.get_current_weather", return_value=mock_weather_data):
        result = get_current_weather.invoke({"city": "Bengaluru"})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data["temperature_c"] == 27.0


def test_currency_tool_invalid_amount_handled():
    result = convert_currency.invoke({"amount": -100, "from_currency": "USD", "to_currency": "INR"})
    assert isinstance(result, ToolResult)
    assert result.success is False
    assert "greater than zero" in result.error


def test_currency_tool_mocked_success():
    mock_curr = {
        "amount": 100.0,
        "from_currency": "USD",
        "to_currency": "INR",
        "converted_amount": 8350.0,
        "exchange_rate": 83.5,
    }
    with patch("app.tools.currency._currency_service.convert_currency", return_value=mock_curr):
        result = convert_currency.invoke({"amount": 100, "from_currency": "USD", "to_currency": "INR"})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data["converted_amount"] == 8350.0


def test_flights_tool_missing_filters_handled():
    result = search_flights.invoke({})
    assert isinstance(result, ToolResult)
    assert result.success is False
    assert "At least one search filter" in result.error


def test_hotels_tool_empty_city_handled():
    result = search_hotels.invoke({"city": ""})
    assert isinstance(result, ToolResult)
    assert result.success is False
    assert "cannot be empty" in result.error


def test_maps_tool_empty_endpoints_handled():
    result = get_route.invoke({"origin": "", "destination": "Bengaluru"})
    assert isinstance(result, ToolResult)
    assert result.success is False
    assert "cannot be empty" in result.error


def test_places_tool_empty_city_handled():
    result = search_places.invoke({"city": ""})
    assert isinstance(result, ToolResult)
    assert result.success is False
    assert "cannot be empty" in result.error


def test_tool_executor_unknown_tool_raises():
    executor = ToolExecutor()
    with pytest.raises(ValueError, match="Unknown tool"):
        executor.execute("unknown_teleportation_tool", {})


def test_tool_executor_successful_execution():
    executor = ToolExecutor()
    mock_weather = {"city": "Paris", "temperature_c": 21.0}
    with patch("app.tools.weather._weather_service.get_current_weather", return_value=mock_weather):
        result = executor.execute("get_current_weather", {"city": "Paris"})
        assert isinstance(result, ToolResult)
        assert result.success is True
        assert result.data["temperature_c"] == 21.0
