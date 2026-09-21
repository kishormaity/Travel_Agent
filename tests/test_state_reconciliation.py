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
