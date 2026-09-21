import pytest
import httpx
from unittest.mock import MagicMock
from pydantic import ValidationError

from app.agents.retry_policy import RetryPolicy
from app.agents.execution_subgraph import (
    run_executor_node,
    route_execution,
    route_validation,
)
from app.schemas.planner.task import Task, TaskStatus
from langgraph.graph import END


def test_retry_policy_is_retryable_transient_network():
    policy = RetryPolicy()
    assert policy.is_retryable(httpx.ConnectError("Connection refused")) is True
    assert policy.is_retryable(httpx.ConnectTimeout("Connect timeout")) is True
    assert policy.is_retryable(httpx.ReadTimeout("Read timeout")) is True
    assert policy.is_retryable(ConnectionError("Socket closed")) is True
    assert policy.is_retryable(TimeoutError("Operation timed out")) is True


def test_retry_policy_is_retryable_server_and_rate_limit():
    policy = RetryPolicy()

    # 503 Service Unavailable
    res_503 = httpx.Response(status_code=503, request=httpx.Request("GET", "https://api.test"))
    err_503 = httpx.HTTPStatusError("503", request=res_503.request, response=res_503)
    assert policy.is_retryable(err_503) is True

    # 429 Rate Limit
    res_429 = httpx.Response(status_code=429, request=httpx.Request("GET", "https://api.test"))
    err_429 = httpx.HTTPStatusError("429", request=res_429.request, response=res_429)
    assert policy.is_retryable(err_429) is True


def test_retry_policy_permanent_failures():
    policy = RetryPolicy()

    # 401 Unauthorized
    res_401 = httpx.Response(status_code=401, request=httpx.Request("GET", "https://api.test"))
    err_401 = httpx.HTTPStatusError("401", request=res_401.request, response=res_401)
    assert policy.is_retryable(err_401) is False

    # 404 Not Found
    res_404 = httpx.Response(status_code=404, request=httpx.Request("GET", "https://api.test"))
    err_404 = httpx.HTTPStatusError("404", request=res_404.request, response=res_404)
    assert policy.is_retryable(err_404) is False

    # Standard permanent errors
    assert policy.is_retryable(ValueError("Invalid argument")) is False
    assert policy.is_retryable(KeyError("missing_key")) is False


def test_retry_policy_unwraps_chained_causes():
    policy = RetryPolicy()
    root_cause = httpx.ConnectError("Network is unreachable")
    wrapped_err = Exception("Outer failure")
    wrapped_err.__cause__ = root_cause

    assert policy.is_retryable(wrapped_err) is True


def test_retry_policy_delay_calculation_and_cap():
    policy = RetryPolicy(
        initial_delay=1.0,
        backoff_factor=2.0,
        max_delay=5.0,
        jitter_min=0.1,
        jitter_max=0.2,
    )

    # Attempt 1: 1.0 + jitter (0.1..0.2)
    d1 = policy.calculate_delay(attempt=1)
    assert 1.1 <= d1 <= 1.2

    # Attempt 2: 2.0 + jitter (0.1..0.2)
    d2 = policy.calculate_delay(attempt=2)
    assert 2.1 <= d2 <= 2.2

    # Attempt 3: 4.0 + jitter (0.1..0.2)
    d3 = policy.calculate_delay(attempt=3)
    assert 4.1 <= d3 <= 4.2

    # Attempt 4: 8.0 capped at max_delay 5.0 + jitter (0.1..0.2)
    d4 = policy.calculate_delay(attempt=4)
    assert 5.1 <= d4 <= 5.2


def test_execution_subgraph_successful_execution(sample_task_factory):
    task = sample_task_factory(1)
    router_mock = MagicMock()
    router_mock.execute.return_value = {"temperature_c": 26.5}

    config = {
        "configurable": {
            "executor_router": router_mock,
            "retry_policy": RetryPolicy(),
        }
    }
    state = {"task": task, "attempt": 0}
    result = run_executor_node(state, config)

    assert result["pipeline_result"].success is True
    assert result["task"].status == TaskStatus.COMPLETED
    assert result["task"].result == {"temperature_c": 26.5}
    assert route_execution(result, config) == END


def test_execution_subgraph_transient_failure_routes_to_backoff(sample_task_factory):
    task = sample_task_factory(1)
    router_mock = MagicMock()
    router_mock.execute.side_effect = httpx.ConnectTimeout("Connection timed out")

    policy = RetryPolicy(max_attempts=3, initial_delay=0.1)
    config = {
        "configurable": {
            "executor_router": router_mock,
            "retry_policy": policy,
        }
    }
    state = {"task": task, "attempt": 0}
    result = run_executor_node(state, config)

    # First attempt should remain RUNNING with retry scheduled
    assert result["pipeline_result"].success is False
    assert result["pipeline_result"].retryable is True
    assert result["task"].status == TaskStatus.RUNNING
    assert result["next_delay"] > 0
    assert route_execution(result, config) == "retry_backoff"


def test_execution_subgraph_permanent_failure_fails_fast(sample_task_factory):
    task = sample_task_factory(1)
    res_401 = httpx.Response(status_code=401, request=httpx.Request("GET", "https://api.test"))
    router_mock = MagicMock()
    router_mock.execute.side_effect = httpx.HTTPStatusError("Unauthorized", request=res_401.request, response=res_401)

    policy = RetryPolicy(max_attempts=3)
    config = {
        "configurable": {
            "executor_router": router_mock,
            "retry_policy": policy,
        }
    }
    state = {"task": task, "attempt": 0}
    result = run_executor_node(state, config)

    # Permanent failure should immediately mark FAILED with no delay and route to END
    assert result["pipeline_result"].success is False
    assert result["pipeline_result"].retryable is False
    assert result["task"].status == TaskStatus.FAILED
    assert result["task"].failure_type == "logical"
    assert result["next_delay"] == 0.0
    assert route_execution(result, config) == END
