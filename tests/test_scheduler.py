import pytest
from langgraph.types import Send
from app.schemas.planner.task import Task, TaskStatus
from app.schemas.planner.execution_plan import ExecutionPlan
from app.agents.graph_nodes import scheduler_node, _propagate_failure
from app.agents.coordinator_agent import route_after_scheduler


def test_scheduler_independent_tasks_concurrently_ready(sample_task_factory, mock_runnable_config):
    # 3 independent tasks
    tasks = {
        1: sample_task_factory(1, tool_name="get_current_weather", depends_on=[]),
        2: sample_task_factory(2, tool_name="search_hotels", depends_on=[]),
        3: sample_task_factory(3, tool_name="convert_currency", depends_on=[]),
    }
    state = {"execution_plan": ExecutionPlan(tasks=tasks)}
    result = scheduler_node(state, mock_runnable_config)
    sched = result["scheduler_result"]

    assert sched.has_ready_tasks is True
    assert set(sched.ready_tasks) == {1, 2, 3}
    assert sched.waiting_tasks == []
    assert sched.blocked_tasks == []
    assert sched.failed_tasks == []
    assert sched.completed_tasks == []


def test_scheduler_dependent_task_waits_for_prerequisite(sample_task_factory, mock_runnable_config):
    # Task 1 is independent, Task 2 depends on Task 1
    tasks = {
        1: sample_task_factory(1, status=TaskStatus.PENDING, depends_on=[]),
        2: sample_task_factory(2, status=TaskStatus.PENDING, depends_on=[1]),
    }
    state = {"execution_plan": ExecutionPlan(tasks=tasks)}
    result = scheduler_node(state, mock_runnable_config)
    sched = result["scheduler_result"]

    assert sched.ready_tasks == [1]
    assert sched.waiting_tasks == [2]

    # Now simulate Task 1 completing
    tasks_after_t1 = dict(result["execution_plan"].tasks)
    tasks_after_t1[1] = tasks_after_t1[1].model_copy(update={"status": TaskStatus.COMPLETED})
    state2 = {"execution_plan": ExecutionPlan(tasks=tasks_after_t1)}
    result2 = scheduler_node(state2, mock_runnable_config)
    sched2 = result2["scheduler_result"]

    assert sched2.ready_tasks == [2]
    assert sched2.waiting_tasks == []
    assert sched2.completed_tasks == [1]


def test_scheduler_multi_parent_dependency(sample_task_factory, mock_runnable_config):
    # Task 3 depends on BOTH Task 1 and Task 2
    tasks = {
        1: sample_task_factory(1, status=TaskStatus.COMPLETED, depends_on=[]),
        2: sample_task_factory(2, status=TaskStatus.RUNNING, depends_on=[]),
        3: sample_task_factory(3, status=TaskStatus.PENDING, depends_on=[1, 2]),
    }
    state = {"execution_plan": ExecutionPlan(tasks=tasks)}
    result = scheduler_node(state, mock_runnable_config)
    sched = result["scheduler_result"]

    # Task 3 must wait because Task 2 is still running
    assert 3 in sched.waiting_tasks
    assert 3 not in sched.ready_tasks


def test_scheduler_recursive_failure_cascade(sample_task_factory, mock_runnable_config):
    # 1 (FAILED) -> 2 (depends on 1) -> 3 (depends on 2)
    tasks = {
        1: sample_task_factory(1, status=TaskStatus.FAILED, error="Connection timed out"),
        2: sample_task_factory(2, status=TaskStatus.PENDING, depends_on=[1]),
        3: sample_task_factory(3, status=TaskStatus.PENDING, depends_on=[2]),
    }
    state = {"execution_plan": ExecutionPlan(tasks=tasks)}
    result = scheduler_node(state, mock_runnable_config)
    updated_tasks = result["execution_plan"].tasks

    # Both downstream tasks must be cascaded to FAILED
    assert updated_tasks[2].status == TaskStatus.FAILED
    assert updated_tasks[2].failure_type == "dependency"
    assert "Parent dependency task 1 failed" in updated_tasks[2].error

    assert updated_tasks[3].status == TaskStatus.FAILED
    assert updated_tasks[3].failure_type == "dependency"
    assert "Parent dependency task 2 failed" in updated_tasks[3].error

    sched = result["scheduler_result"]
    assert set(sched.failed_tasks) == {1, 2, 3}
    assert sched.ready_tasks == []


def test_route_after_scheduler_dispatches_sends(sample_task_factory):
    tasks = {
        1: sample_task_factory(1, status=TaskStatus.READY),
        2: sample_task_factory(2, status=TaskStatus.READY),
    }
    from app.agents.graph_state import SchedulerResult
    state = {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "scheduler_result": SchedulerResult(
            has_ready_tasks=True,
            ready_tasks=[1, 2],
        ),
        "replan_count": 0,
        "max_replan_attempts": 3,
        "execution_policy": "best_effort",
    }
    routes = route_after_scheduler(state)
    assert isinstance(routes, list)
    assert len(routes) == 2
    assert all(isinstance(r, Send) for r in routes)
    assert routes[0].node == "execute_task"
    assert routes[0].arg["task_id"] == 1
    assert routes[1].arg["task_id"] == 2


def test_route_after_scheduler_completes_when_all_done(sample_task_factory):
    tasks = {
        1: sample_task_factory(1, status=TaskStatus.COMPLETED),
    }
    from app.agents.graph_state import SchedulerResult
    state = {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "scheduler_result": SchedulerResult(
            has_ready_tasks=False,
            completed_tasks=[1],
        ),
        "replan_count": 0,
        "max_replan_attempts": 3,
    }
    route = route_after_scheduler(state)
    assert route == "responder"
