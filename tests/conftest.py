import pytest
from unittest.mock import MagicMock
from app.schemas.planner.task import Task, TaskStatus
from app.schemas.planner.execution_plan import ExecutionPlan, PlanStatus
from app.agents.graph_state import ValidationResult, SchedulerResult


@pytest.fixture
def sample_task_factory():
    def _create(
        task_id: int,
        tool_name: str = "get_current_weather",
        description: str = "Test task",
        arguments: dict = None,
        depends_on: list[int] = None,
        status: TaskStatus = TaskStatus.PENDING,
        priority: int = 1,
        error: str = None,
        failure_type: str = None,
    ) -> Task:
        return Task(
            id=task_id,
            tool_name=tool_name,
            description=description,
            arguments=arguments if arguments is not None else {"city": "Bengaluru"},
            depends_on=depends_on or [],
            status=status,
            priority=priority,
            error=error,
            failure_type=failure_type,
        )

    return _create


@pytest.fixture
def mock_runnable_config():
    return {
        "configurable": {
            "thread_id": "test-session",
            "model_name": "llama-3.3-70b-versatile",
            "conversation_memory": MagicMock(),
            "llm_client": MagicMock(),
            "response_agent": MagicMock(),
            "executor_router": MagicMock(),
            "retry_policy": MagicMock(),
            "user_request": "Test trip",
        }
    }
