import pytest
from app.schemas.planner.task import Task, TaskStatus
from app.schemas.planner.execution_plan import ExecutionPlan
from app.agents.graph_nodes import plan_validator_node, _detect_dependency_cycles
from app.agents.graph_state import ValidationErrorType, Recoverability


def test_detect_dependency_cycles_valid_linear(sample_task_factory):
    # 1 -> 2 -> 3 (no cycle)
    tasks = {
        1: sample_task_factory(1, depends_on=[]),
        2: sample_task_factory(2, depends_on=[1]),
        3: sample_task_factory(3, depends_on=[2]),
    }
    # Should not raise
    _detect_dependency_cycles(tasks)


def test_detect_dependency_cycles_direct_cycle(sample_task_factory):
    # 1 -> 2 -> 1 (cycle)
    tasks = {
        1: sample_task_factory(1, depends_on=[2]),
        2: sample_task_factory(2, depends_on=[1]),
    }
    with pytest.raises(ValueError, match="Dependency cycle detected"):
        _detect_dependency_cycles(tasks)


def test_detect_dependency_cycles_indirect_cycle(sample_task_factory):
    # 1 -> 2 -> 3 -> 1 (cycle)
    tasks = {
        1: sample_task_factory(1, depends_on=[3]),
        2: sample_task_factory(2, depends_on=[1]),
        3: sample_task_factory(3, depends_on=[2]),
    }
    with pytest.raises(ValueError, match="Dependency cycle detected"):
        _detect_dependency_cycles(tasks)


def test_plan_validator_node_valid_plan(sample_task_factory, mock_runnable_config):
    tasks = {
        1: sample_task_factory(1, tool_name="get_current_weather", arguments={"city": "Bengaluru"}),
        2: sample_task_factory(2, tool_name="search_hotels", arguments={"city": "Bengaluru"}, depends_on=[1]),
    }
    state = {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "validation_result": None,
    }
    result = plan_validator_node(state, mock_runnable_config)
    assert result["validation_result"].valid is True


def test_plan_validator_node_cycle_detected(sample_task_factory, mock_runnable_config):
    tasks = {
        1: sample_task_factory(1, depends_on=[2]),
        2: sample_task_factory(2, depends_on=[1]),
    }
    state = {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "validation_result": None,
    }
    result = plan_validator_node(state, mock_runnable_config)
    assert result["validation_result"].valid is False
    assert result["validation_result"].error_type == ValidationErrorType.CIRCULAR_REFERENCE
    assert result["validation_result"].recoverable == Recoverability.RECOVERABLE


def test_plan_validator_node_self_dependency(sample_task_factory, mock_runnable_config):
    tasks = {
        1: sample_task_factory(1, depends_on=[1]),
    }
    state = {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "validation_result": None,
    }
    result = plan_validator_node(state, mock_runnable_config)
    assert result["validation_result"].valid is False
    assert result["validation_result"].error_type == ValidationErrorType.INVALID_DEPENDENCY


def test_plan_validator_node_unknown_dependency(sample_task_factory, mock_runnable_config):
    tasks = {
        1: sample_task_factory(1, depends_on=[999]),
    }
    state = {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "validation_result": None,
    }
    result = plan_validator_node(state, mock_runnable_config)
    assert result["validation_result"].valid is False
    assert result["validation_result"].error_type == ValidationErrorType.UNKNOWN_DEPENDENCY


def test_plan_validator_node_unknown_tool(sample_task_factory, mock_runnable_config):
    tasks = {
        1: sample_task_factory(1, tool_name="nonexistent_teleport_tool", arguments={}),
    }
    state = {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "validation_result": None,
    }
    result = plan_validator_node(state, mock_runnable_config)
    assert result["validation_result"].valid is False
    assert result["validation_result"].error_type == ValidationErrorType.UNKNOWN_TOOL


def test_plan_validator_node_missing_arguments(sample_task_factory, mock_runnable_config):
    # get_current_weather requires 'city'
    tasks = {
        1: sample_task_factory(1, tool_name="get_current_weather", arguments={}),
    }
    state = {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "validation_result": None,
    }
    result = plan_validator_node(state, mock_runnable_config)
    assert result["validation_result"].valid is False
    assert result["validation_result"].error_type == ValidationErrorType.INVALID_ARGUMENTS


def test_plan_validator_node_llm_reasoning_allowed(sample_task_factory, mock_runnable_config):
    tasks = {
        1: sample_task_factory(1, tool_name="llm_reasoning", arguments={"description": "Synthesize plan"}),
    }
    state = {
        "execution_plan": ExecutionPlan(tasks=tasks),
        "validation_result": None,
    }
    result = plan_validator_node(state, mock_runnable_config)
    assert result["validation_result"].valid is True
