import json
import pytest
from uuid import uuid4
from unittest.mock import MagicMock

from app.schemas.planner.task import Task, TaskStatus
from app.schemas.planner.execution_plan import ExecutionPlan, PlanStatus
from app.agents.graph_state import merge_tasks, merge_plans
from app.agents.planner_subgraph import parse_and_map_node


def test_merge_tasks_adds_and_updates(sample_task_factory):
    existing = {
        1: sample_task_factory(1, status=TaskStatus.RUNNING),
    }
    update = {
        1: sample_task_factory(1, status=TaskStatus.COMPLETED, arguments={"city": "Bengaluru"}),
        2: sample_task_factory(2, status=TaskStatus.PENDING),
    }

    merged = merge_tasks(existing, update)
    assert len(merged) == 2
    assert merged[1].status == TaskStatus.COMPLETED
    assert merged[2].status == TaskStatus.PENDING


def test_merge_plans_preserves_identity_and_updates_tasks(sample_task_factory):
    p_id = uuid4()
    plan1 = ExecutionPlan(
        plan_id=p_id,
        tasks={1: sample_task_factory(1, status=TaskStatus.RUNNING)},
        version=1,
    )

    update_plan = ExecutionPlan(
        tasks={1: sample_task_factory(1, status=TaskStatus.COMPLETED)},
        version=2,
        parent_version=1,
        planning_rationale="Updated task",
    )

    merged = merge_plans(plan1, update_plan)
    assert merged.plan_id == p_id
    assert merged.version == 2
    assert merged.parent_version == 1
    assert merged.tasks[1].status == TaskStatus.COMPLETED


def test_parse_and_map_node_replan_merges_history(sample_task_factory, mock_runnable_config):
    # Existing completed task from initial plan
    task1 = sample_task_factory(1, description="Initial flight search", status=TaskStatus.COMPLETED)
    existing_plan = ExecutionPlan(
        tasks={1: task1},
        version=1,
    )

    # LLM proposes a new task in replanning, depending on task 1
    llm_output = json.dumps({
        "tasks": [
            {
                "description": "Book hotel near airport",
                "tool_name": "search_hotels",
                "arguments": {"city": "Bengaluru"},
                "depends_on": [1],
                "priority": 1,
            }
        ]
    })

    state = {
        "llm_response": llm_output,
        "replan_count": 1,
        "execution_plan": existing_plan,
    }

    result = parse_and_map_node(state, mock_runnable_config)
    new_plan = result["execution_plan"]

    # History preservation check: task 1 must still exist!
    assert 1 in new_plan.tasks
    assert new_plan.tasks[1].status == TaskStatus.COMPLETED

    # Sequential ID assignment check: new task must have ID 2 (max_existing_id + 1)
    assert 2 in new_plan.tasks
    assert new_plan.tasks[2].id == 2
    assert new_plan.tasks[2].description == "Book hotel near airport"
    assert new_plan.tasks[2].depends_on == [1]

    # Version lineage check
    assert new_plan.version == 2
    assert new_plan.parent_version == 1
    assert result["validation_result"].valid is True


def test_parse_and_map_non_sequential_existing_ids(sample_task_factory, mock_runnable_config):
    """Verify replanning handles non-sequential historical task IDs (e.g., 5, 12)."""
    task5 = sample_task_factory(5, description="Search flight to Jaipur", status=TaskStatus.COMPLETED)
    task12 = sample_task_factory(12, description="Check weather in Jaipur", status=TaskStatus.COMPLETED)
    existing_plan = ExecutionPlan(tasks={5: task5, 12: task12}, version=1)

    llm_output = json.dumps({
        "tasks": [
            {
                "description": "Book heritage hotel",
                "tool_name": "search_hotels",
                "arguments": {"city": "Jaipur"},
                "depends_on": [5, 12],
                "priority": 1,
            }
        ]
    })

    state = {
        "llm_response": llm_output,
        "replan_count": 1,
        "execution_plan": existing_plan,
    }

    result = parse_and_map_node(state, mock_runnable_config)
    new_plan = result["execution_plan"]

    # Historical tasks preserved
    assert 5 in new_plan.tasks and new_plan.tasks[5].status == TaskStatus.COMPLETED
    assert 12 in new_plan.tasks and new_plan.tasks[12].status == TaskStatus.COMPLETED

    # New task assigned max_id + 1 = 13
    assert 13 in new_plan.tasks
    assert new_plan.tasks[13].id == 13
    assert set(new_plan.tasks[13].depends_on) == {5, 12}


def test_parse_and_map_multiple_dependencies(sample_task_factory, mock_runnable_config):
    """Verify newly generated task correctly preserves multiple dependencies."""
    t1 = sample_task_factory(1, description="Flight", status=TaskStatus.COMPLETED)
    t2 = sample_task_factory(2, description="Weather", status=TaskStatus.COMPLETED)
    existing_plan = ExecutionPlan(tasks={1: t1, 2: t2}, version=1)

    llm_output = json.dumps({
        "tasks": [
            {
                "description": "Plan itinerary",
                "tool_name": "search_places",
                "arguments": {"city": "Jaipur"},
                "depends_on": [1, 2],
                "priority": 1,
            }
        ]
    })

    state = {
        "llm_response": llm_output,
        "replan_count": 1,
        "execution_plan": existing_plan,
    }

    result = parse_and_map_node(state, mock_runnable_config)
    new_plan = result["execution_plan"]

    assert 3 in new_plan.tasks
    assert set(new_plan.tasks[3].depends_on) == {1, 2}


def test_replan_max_replan_limit_bounds_execution(sample_task_factory):
    """Verify route_after_scheduler terminates to responder when max_replan_attempts is reached."""
    from app.agents.coordinator_agent import route_after_scheduler
    from app.agents.graph_state import SchedulerResult

    t1 = sample_task_factory(1, status=TaskStatus.FAILED, error="Timeout")
    plan = ExecutionPlan(tasks={1: t1})
    scheduler_result = SchedulerResult(
        ready_tasks=[],
        running_tasks=[],
        completed_tasks=[],
        failed_tasks=[1],
        waiting_tasks=[],
        blocked_tasks=[],
    )

    state = {
        "execution_plan": plan,
        "scheduler_result": scheduler_result,
        "replan_count": 3,
        "max_replan_attempts": 3,
        "execution_policy": "best_effort",
    }

    next_route = route_after_scheduler(state)
    assert next_route == "responder", f"Expected 'responder' at max replans, got '{next_route}'"


def test_completed_task_deduplication_during_replanning(sample_task_factory, mock_runnable_config):
    """Verify replanning does not create duplicate pending tasks for already completed operations."""
    t1 = sample_task_factory(
        1,
        description="Search flights from DEL to COK",
        tool_name="search_flights",
        arguments={"origin": "DEL", "destination": "COK", "flight_date": "2027-01-10"},
        status=TaskStatus.COMPLETED,
    )
    t1.result = [{"flight": "AI547", "price": 25000}]
    existing_plan = ExecutionPlan(tasks={1: t1}, version=1)

    # LLM re-proposes the identical flight search in replanning
    llm_output = json.dumps({
        "tasks": [
            {
                "description": "Search flights from DEL to COK",
                "tool_name": "search_flights",
                "arguments": {"origin": "DEL", "destination": "COK", "flight_date": "2027-01-10"},
                "depends_on": [],
                "priority": 1,
            },
            {
                "description": "Find hotel in Kochi",
                "tool_name": "search_hotels",
                "arguments": {"city": "Kochi"},
                "depends_on": [1],
                "priority": 2,
            }
        ]
    })

    state = {
        "llm_response": llm_output,
        "replan_count": 1,
        "execution_plan": existing_plan,
    }

    result = parse_and_map_node(state, mock_runnable_config)
    new_plan = result["execution_plan"]

    # Only 1 flight task should exist, and it must remain COMPLETED with its original result!
    assert len(new_plan.tasks) == 2
    assert new_plan.tasks[1].status == TaskStatus.COMPLETED
    assert new_plan.tasks[1].result == [{"flight": "AI547", "price": 25000}]
    assert 2 in new_plan.tasks
    assert new_plan.tasks[2].description == "Find hotel in Kochi"
    assert new_plan.tasks[2].depends_on == [1]

