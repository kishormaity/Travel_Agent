import time
import random
import httpx
from typing import TypedDict, Any
from loguru import logger
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END

from app.agents.graph_state import (
    TaskExecutionResult,
    ExecutorResult,
    ExecutorMetadata,
    RetryPolicy,
    TaskStatus,
    ExecutionPlan,
)
from app.schemas.planner.task import Task

class TaskExecutionState(TypedDict):
    # Inputs from Parent
    task_id: int
    task: Task
    
    # Outputs returned to Parent
    execution_plan: ExecutionPlan
    pipeline_result: TaskExecutionResult
    
    # Internal Pipeline State
    attempt: int
    next_delay: float
    error_message: str | None
    executor_result: ExecutorResult | None

def validate_task_node(state: TaskExecutionState) -> dict:
    """Initializes local state values and validates tool configuration."""
    task = state["task"]
    attempt = state.get("attempt", 0)
    
    from app.registry.tool_registry import AVAILABLE_TOOLS
    if task.tool_name not in AVAILABLE_TOOLS:
        err = f"Validation Error: Unknown tool {task.tool_name}"
        failed_task = task.model_copy(update={"status": TaskStatus.FAILED, "error": err})
        result = TaskExecutionResult(
            task=failed_task,
            success=False,
            retryable=False,
            error=err
        )
        return {
            "attempt": attempt, 
            "pipeline_result": result,
            "execution_plan": ExecutionPlan(tasks={task.id: failed_task})
        }
        
    return {"attempt": attempt}

def run_executor_node(state: TaskExecutionState, config: RunnableConfig) -> dict:
    """Executes the task using ExecutorRouter with error isolation and timing metrics."""
    task = state["task"]
    attempt = state.get("attempt", 0) + 1
    
    # Update task status to RUNNING
    task_running = task.model_copy(update={
        "status": TaskStatus.RUNNING,
        "worker_id": task.id
    })

    # Emit progress callback
    on_progress = config["configurable"].get("on_progress")
    if on_progress:
        from app.schemas.planner.progress_event import ProgressEvent
        try:
            on_progress(ProgressEvent(
                task_id=task_running.id,
                description=task_running.description,
                tool_name=task_running.tool_name,
                status=task_running.status,
                worker_id=task_running.worker_id,
                retry_count=attempt - 1
            ))
        except Exception as p_err:
            logger.warning(f"Progress event callback error: {p_err}")

    # Set up start timing
    start_time = time.time()
    executor_router = config["configurable"].get("executor_router")
    
    try:
        # Run tool
        user_request = state.get("user_request") or config["configurable"].get("user_request")
        output = executor_router.execute(task_running, user_request=user_request)
        latency = (time.time() - start_time) * 1000.0
        
        # Complete task status updates
        completed_task = task_running.model_copy(update={
            "status": TaskStatus.COMPLETED,
            "result": output,
            "error": None
        })
        
        exec_metadata = ExecutorMetadata(
            latency_ms=latency,
            provider="local_registry"
        )
        
        exec_result = ExecutorResult(
            success=True,
            output=output,
            metadata=exec_metadata
        )
        
        pipeline_result = TaskExecutionResult(
            task=completed_task,
            success=True,
            executor_result=exec_result
        )
        
        if on_progress:
            from app.schemas.planner.progress_event import ProgressEvent
            try:
                on_progress(ProgressEvent(
                    task_id=task.id,
                    description=task.description,
                    tool_name=task.tool_name,
                    status=TaskStatus.COMPLETED,
                    execution_time=time.time() - start_time,
                    worker_id=task.id,
                    retry_count=attempt - 1
                ))
            except Exception as p_err:
                logger.warning(f"Progress callback completion error: {p_err}")
                
        return {
            "task": completed_task,
            "attempt": attempt,
            "executor_result": exec_result,
            "pipeline_result": pipeline_result,
            "execution_plan": ExecutionPlan(tasks={task.id: completed_task})
        }
        
    except Exception as e:
        latency = (time.time() - start_time) * 1000.0
        
        # Determine retry capability for exception type
        is_retryable = False
        if isinstance(e, (httpx.RequestError, httpx.HTTPStatusError, TimeoutError, ConnectionError)):
            is_retryable = True
            
        retry_policy = config["configurable"].get("retry_policy", RetryPolicy())
        
        # If retryable and attempt limit not reached, keep status RUNNING/PENDING and compute backoff delay
        if is_retryable and attempt < retry_policy.max_attempts:
            task_status = TaskStatus.RUNNING
            delay = retry_policy.initial_delay * (retry_policy.backoff_factor ** (attempt - 1))
            jitter = random.uniform(retry_policy.jitter_min, retry_policy.jitter_max)
            next_delay = delay + jitter
        else:
            task_status = TaskStatus.FAILED
            next_delay = 0.0
            
        logger.warning(f"Task {task.id} attempt {attempt} failed: {e}. Retryable: {is_retryable}")
        
        failed_task = task_running.model_copy(update={
            "status": task_status,
            "error": str(e)
        })
        
        exec_metadata = ExecutorMetadata(
            latency_ms=latency,
            provider="local_registry"
        )
        
        exec_result = ExecutorResult(
            success=False,
            error=str(e),
            retryable=is_retryable,
            metadata=exec_metadata
        )
        
        pipeline_result = TaskExecutionResult(
            task=failed_task,
            success=False,
            retryable=is_retryable,
            error=str(e),
            executor_result=exec_result
        )
        
        if task_status == TaskStatus.FAILED:
            if on_progress:
                from app.schemas.planner.progress_event import ProgressEvent
                try:
                    on_progress(ProgressEvent(
                        task_id=task.id,
                        description=task.description,
                        tool_name=task.tool_name,
                        status=TaskStatus.FAILED,
                        execution_time=time.time() - start_time,
                        worker_id=task.id,
                        retry_count=attempt - 1,
                        error=str(e)
                    ))
                except Exception as p_err:
                    logger.warning(f"Progress callback failure error: {p_err}")
                    
        return {
            "task": failed_task,
            "attempt": attempt,
            "next_delay": next_delay,
            "executor_result": exec_result,
            "pipeline_result": pipeline_result,
            "execution_plan": ExecutionPlan(tasks={task.id: failed_task})
        }

def retry_backoff_node(state: TaskExecutionState, config: RunnableConfig) -> dict:
    """Performs thread sleeping to implement exponential backoff."""
    next_delay = state.get("next_delay", 1.0)
    logger.info(f"Task {state['task'].id} retrying: sleeping for {next_delay:.2f}s...")
    time.sleep(next_delay)
    return {}

# Define Edge Routers
def route_validation(state: TaskExecutionState) -> str:
    res = state.get("pipeline_result")
    if res and not res.success:
        return END
    return "run_executor"

def route_execution(state: TaskExecutionState, config: RunnableConfig) -> str:
    res = state.get("pipeline_result")
    if not res:
        return END
        
    if res.success:
        return END
        
    retry_policy = config["configurable"].get("retry_policy", RetryPolicy())
    attempt = state.get("attempt", 0)
    
    if res.retryable and attempt < retry_policy.max_attempts:
        return "retry_backoff"
        
    return END

# Build Subgraph
builder = StateGraph(TaskExecutionState)
builder.add_node("validate_task", validate_task_node)
builder.add_node("run_executor", run_executor_node)
builder.add_node("retry_backoff", retry_backoff_node)

builder.add_edge(START, "validate_task")
builder.add_conditional_edges(
    "validate_task",
    route_validation,
    {
        END: END,
        "run_executor": "run_executor",
    }
)
builder.add_conditional_edges(
    "run_executor",
    route_execution,
    {
        END: END,
        "retry_backoff": "retry_backoff",
    }
)
builder.add_edge("retry_backoff", "run_executor")

execute_task_subgraph = builder.compile()
