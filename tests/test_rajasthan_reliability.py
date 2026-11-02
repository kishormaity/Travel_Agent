import json
import pytest
from unittest.mock import MagicMock, patch

from app.services.request_normalizer import resolve_airport_code, normalize_city_name
from app.tools.weather import normalize_weather_city, get_current_weather
from app.tools.flights import search_flights
from app.agents.flight.agent import FlightAgent
from app.schemas.tool_result import ToolResult
from app.schemas.planner.task import Task, TaskStatus
from app.schemas.planner.execution_plan import ExecutionPlan, PlanStatus
from app.schemas.planner.planner_response import PlannerResponse, PlannerTask
from app.agents.planner_subgraph import parse_and_map_node, _is_task_equivalent
from app.agents.response_agent import format_flight_results_for_response


# ==============================================================================
# 1. Airport Code Normalization Tests
# ==============================================================================

def test_udaipur_resolves_to_udr():
    """Verify that Udaipur resolves to UDR in all forms and casing."""
    assert resolve_airport_code("Udaipur") == "UDR"
    assert resolve_airport_code("udaipur") == "UDR"
    assert resolve_airport_code("UDR") == "UDR"
    assert resolve_airport_code("udr") == "UDR"


def test_invalid_udi_code_corrected_to_udr():
    """Verify that hallucinated/invalid code 'UDI' is corrected to 'UDR'."""
    assert resolve_airport_code("UDI") == "UDR"
    assert resolve_airport_code("udi") == "UDR"


def test_jodhpur_and_jaipur_airport_codes():
    """Verify that Jodhpur resolves to JDH and Jaipur to JAI."""
    assert resolve_airport_code("Jodhpur") == "JDH"
    assert resolve_airport_code("jodhpur") == "JDH"
    assert resolve_airport_code("jodhur") == "JDH"  # Typo correction
    assert resolve_airport_code("Jaipur") == "JAI"
    assert resolve_airport_code("jaipur") == "JAI"


def test_flight_agent_intercepts_udi_destination():
    """Verify that FlightAgent automatically corrects arrival_iata='UDI' to 'UDR'."""
    FlightAgent.clear_cache()
    agent = FlightAgent()

    with patch("app.mcp.remote.remote_mcp_manager.ensure_initialized"), \
         patch("app.mcp.remote.remote_mcp_manager._tools_cache", {"flight_octotrip_search": MagicMock()}), \
         patch("app.mcp.remote.remote_mcp_manager.execute_tool") as mock_exec:

        mock_exec.return_value = {
            "success": True,
            "data": [{"type": "text", "text": json.dumps({"results": []})}],
        }

        agent.execute(
            departure_iata="DEL",
            arrival_iata="UDI",  # Invalid hallucinated code
            flight_date="2026-12-10",
            bypass_cache=True,
        )

        # Assert remote MCP tool was called with UDR, not UDI
        call_args = mock_exec.call_args[1]["arguments"]
        assert call_args["destination"] == "UDR"
        assert call_args["origin"] == "DEL"


# ==============================================================================
# 2. Weather City Spelling Normalization Tests
# ==============================================================================

def test_weather_city_normalization_jodhur_to_jodhpur():
    """Verify that common typo 'Jodhur' normalizes to 'Jodhpur'."""
    assert normalize_weather_city("Jodhur") == "Jodhpur"
    assert normalize_weather_city("jodhur") == "Jodhpur"
    assert normalize_weather_city("jodhpu") == "Jodhpur"
    assert normalize_weather_city("jodpur") == "Jodhpur"
    assert normalize_weather_city("Jodhpur, Rajasthan") == "Jodhpur"


def test_weather_city_normalization_other_cities():
    """Verify that other common Indian city spellings are normalized."""
    assert normalize_weather_city("jaipue") == "Jaipur"
    assert normalize_weather_city("udipur") == "Udaipur"
    assert normalize_weather_city("kolkatta") == "Kolkata"
    assert normalize_weather_city("Jaipur") == "Jaipur"
    assert normalize_weather_city("Udaipur") == "Udaipur"


def test_get_current_weather_tool_corrects_spelling():
    """Verify that get_current_weather tool invokes weather service with corrected spelling."""
    with patch("app.tools.weather._weather_service.get_current_weather") as mock_ws:
        mock_ws.return_value = {"city": "Jodhpur", "temperature_c": 28.0, "condition": "Sunny"}
        res = get_current_weather.invoke({"city": "Jodhur"})
        assert res.success is True
        mock_ws.assert_called_once_with("Jodhpur")


# ==============================================================================
# 3. Outbound and Return Flight Pairing & Distinction Tests
# ==============================================================================

def test_format_flight_results_pairs_outbound_and_return():
    """Verify that round-trip flights explicitly pair outbound and return journeys."""
    raw_flight = {
        "airline": "IndiGo",
        "flight_numbers": ["6E201", "6E202"],
        "price": 8500.0,
        "currency": "INR",
        "is_round_trip": True,
        "origin": "DEL",
        "destination": "JAI",
        "departure_date": "2026-12-10",
        "departure_time": "06:00",
        "arrival_date": "2026-12-10",
        "arrival_time": "07:05",
        "return_origin": "JAI",
        "return_destination": "DEL",
        "return_departure_date": "2026-12-17",
        "return_departure_time": "19:00",
        "return_arrival_date": "2026-12-17",
        "return_arrival_time": "20:05",
        "baggage": "Checked bag: 15kg, Cabin: 7kg",
        "booking_url": "https://example.com/book",
    }

    summary = format_flight_results_for_response([raw_flight])
    assert summary["itinerary_type"] == "Round-Trip"
    opt = summary["verified_flight_options"][0]
    assert opt["flight_type"] == "COMPLETE ROUND-TRIP ITINERARY"
    assert "outbound_journey" in opt
    assert "return_journey" in opt
    assert opt["outbound_journey"]["route"] == "DEL -> JAI"
    assert opt["return_journey"]["route"] == "JAI -> DEL"
    assert opt["outbound_journey"]["departure"] == "2026-12-10 06:00"
    assert opt["return_journey"]["departure"] == "2026-12-17 19:00"


def test_format_flight_results_distinguishes_one_way():
    """Verify that one-way flights are clearly distinguished from round-trip itineraries."""
    raw_flight = {
        "airline": "Air India",
        "flight_numbers": ["AI491"],
        "price": 4200.0,
        "currency": "INR",
        "is_round_trip": False,
        "origin": "DEL",
        "destination": "UDR",
        "departure_date": "2026-12-10",
        "departure_time": "14:00",
        "arrival_date": "2026-12-10",
        "arrival_time": "15:20",
        "baggage": "Checked bag: 15kg",
    }

    summary = format_flight_results_for_response([raw_flight])
    assert summary["itinerary_type"] == "One-Way"
    opt = summary["verified_flight_options"][0]
    assert "ONE-WAY" in opt["flight_type"]
    assert "return_journey" not in opt
    assert opt["outbound_journey"]["route"] == "DEL -> UDR"


# ==============================================================================
# 4. Duplicate Task Execution Prevention Across Replanning Tests
# ==============================================================================

def test_task_equivalence_checker():
    """Verify that tasks with identical semantic operations evaluate as equivalent."""
    assert _is_task_equivalent(
        "search_flights", {"departure_iata": "DEL", "arrival_iata": "JAI", "flight_date": "2026-12-10"},
        "search_flights", {"departure_iata": "del", "arrival_iata": "JAI", "flight_date": "2026-12-10"}
    ) is True

    # Hallucinated UDI resolves to UDR, matching UDR task
    assert _is_task_equivalent(
        "search_flights", {"departure_iata": "DEL", "arrival_iata": "UDR", "flight_date": "2026-12-10"},
        "search_flights", {"departure_iata": "DEL", "arrival_iata": "UDI", "flight_date": "2026-12-10"}
    ) is True

    assert _is_task_equivalent(
        "search_hotels", {"city": "Jaipur"},
        "search_hotels", {"city": "jaipur"}
    ) is True

    assert _is_task_equivalent(
        "get_current_weather", {"city": "Jodhpur"},
        "get_current_weather", {"city": "jodhur"}
    ) is True


def test_completed_tasks_not_re_executed_during_replanning():
    """Verify that already COMPLETED tasks are preserved and NOT scheduled as new pending tasks."""
    # Existing plan with Task 1 (Flights, COMPLETED), Task 2 (Hotels, COMPLETED), Task 3 (Weather, FAILED)
    completed_flights_output = [{"airline": "IndiGo", "flight_number": "6E201", "price": 5000.0}]
    completed_hotels_output = [{"hotel": "Taj Rambagh Palace", "price": 25000.0}]

    task1 = Task(
        id=1,
        description="Search flights DEL to JAI",
        tool_name="search_flights",
        arguments={"departure_iata": "DEL", "arrival_iata": "JAI", "flight_date": "2026-12-10"},
        status=TaskStatus.COMPLETED,
        result=completed_flights_output,
    )
    task2 = Task(
        id=2,
        description="Search hotels in Jaipur",
        tool_name="search_hotels",
        arguments={"city": "Jaipur"},
        status=TaskStatus.COMPLETED,
        result=completed_hotels_output,
    )
    task3 = Task(
        id=3,
        description="Get weather for Jodhur",
        tool_name="get_current_weather",
        arguments={"city": "Jodhur"},
        status=TaskStatus.FAILED,
        error="Location not found: Jodhur",
    )

    existing_plan = ExecutionPlan(
        tasks={1: task1, 2: task2, 3: task3},
        version=1,
        plan_status=PlanStatus.ACTIVE,
    )

    # Replanner LLM produces: Task 1 (flights again), Task 2 (hotels again), and Task 3 (corrected weather for Jodhpur)
    replanner_llm_json = json.dumps({
        "tasks": [
            {
                "description": "Search flights DEL to JAI",
                "tool_name": "search_flights",
                "arguments": {"departure_iata": "DEL", "arrival_iata": "JAI", "flight_date": "2026-12-10"},
                "depends_on": [],
                "priority": 1,
            },
            {
                "description": "Search hotels in Jaipur",
                "tool_name": "search_hotels",
                "arguments": {"city": "Jaipur"},
                "depends_on": [],
                "priority": 1,
            },
            {
                "description": "Get weather for Jodhpur",
                "tool_name": "get_current_weather",
                "arguments": {"city": "Jodhpur"},
                "depends_on": [],
                "priority": 2,
            },
        ]
    })

    state = {
        "llm_response": replanner_llm_json,
        "replan_count": 1,
        "execution_plan": existing_plan,
        "user_request": "Plan trip to Rajasthan",
    }
    config = {"configurable": {"model_name": "test-planner"}}

    result = parse_and_map_node(state, config)
    out_plan: ExecutionPlan = result["execution_plan"]

    # Assert Task 1 and Task 2 remained COMPLETED with their original outputs preserved
    assert 1 in out_plan.tasks
    assert out_plan.tasks[1].status == TaskStatus.COMPLETED
    assert out_plan.tasks[1].result == completed_flights_output

    assert 2 in out_plan.tasks
    assert out_plan.tasks[2].status == TaskStatus.COMPLETED
    assert out_plan.tasks[2].result == completed_hotels_output

    # Assert NO duplicate pending tasks were created for flights or hotels
    pending_tasks = [t for t in out_plan.tasks.values() if t.status == TaskStatus.PENDING]
    assert len(pending_tasks) == 1
    assert pending_tasks[0].tool_name == "get_current_weather"
    assert pending_tasks[0].arguments["city"] == "Jodhpur"


# ==============================================================================
# 5. OctoTrip Caching & Bounded Retries Tests
# ==============================================================================

def test_flight_agent_cache_deduplication():
    """Verify that repeated flight search queries hit the in-memory cache without calling remote MCP."""
    FlightAgent.clear_cache()
    agent = FlightAgent()

    mock_offers = {
        "success": True,
        "data": [{
            "type": "text",
            "text": json.dumps({
                "results": [{
                    "airline": "THAI Airways",
                    "price": 50000.0,
                    "currency": "INR",
                    "is_direct": True,
                    "outbound": {
                        "departure": "DEL",
                        "arrival": "BKK",
                        "departure_time": "10:00",
                        "arrival_time": "15:00",
                        "departure_date": "2026-12-10",
                        "arrival_date": "2026-12-10",
                    }
                }]
            })
        }]
    }

    with patch("app.mcp.remote.remote_mcp_manager.ensure_initialized"), \
         patch("app.mcp.remote.remote_mcp_manager._tools_cache", {"flight_octotrip_search": MagicMock()}), \
         patch("app.mcp.remote.remote_mcp_manager.execute_tool") as mock_exec:

        mock_exec.return_value = mock_offers

        # First execution -> calls remote MCP tool
        out1 = agent.execute(departure_iata="DEL", arrival_iata="BKK", flight_date="2026-12-10")
        assert out1.success is True
        assert mock_exec.call_count == 1

        # Second execution with identical args -> returns cached output without calling remote MCP
        out2 = agent.execute(departure_iata="DEL", arrival_iata="BKK", flight_date="2026-12-10")
        assert out2.success is True
        assert mock_exec.call_count == 1  # Still 1! Remote MCP was NOT called again.
        assert len(out2.flights) == len(out1.flights)


def test_flight_agent_bounded_retries_on_timeout():
    """Verify that FlightAgent retries up to 2 times on transient 504 timeouts before failing."""
    FlightAgent.clear_cache()
    agent = FlightAgent()

    with patch("app.mcp.remote.remote_mcp_manager.ensure_initialized"), \
         patch("app.mcp.remote.remote_mcp_manager._tools_cache", {"flight_octotrip_search": MagicMock()}), \
         patch("time.sleep") as mock_sleep, \
         patch("app.mcp.remote.remote_mcp_manager.execute_tool") as mock_exec:

        # Remote MCP returns 504 timeout on first 2 calls, then succeeds on 3rd attempt
        success_response = {
            "success": True,
            "data": [{
                "type": "text",
                "text": json.dumps({"results": []})
            }]
        }
        mock_exec.side_effect = [
            {"success": False, "error": "Remote MCP HTTP 504 Gateway Timeout"},
            {"success": False, "error": "Remote MCP HTTP 504 Gateway Timeout"},
            success_response,
        ]

        out = agent.execute(
            departure_iata="DEL",
            arrival_iata="UDR",
            flight_date="2026-12-10",
            bypass_cache=True,
        )

        assert mock_exec.call_count == 3
        assert mock_sleep.call_count == 2
        assert out.success is True
