import time
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import Annotated, TypedDict, Any
from pydantic import BaseModel, Field

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from app.schemas.planner.task import Task, TaskStatus
from app.agents.retry_policy import RetryPolicy

# ==========================
# Enums
# ==========================

class ValidationErrorType(str, Enum):
    CIRCULAR_REFERENCE = "circular_reference"
    UNKNOWN_DEPENDENCY = "unknown_dependency"
    INVALID_DEPENDENCY = "invalid_dependency"
    DUPLICATE_TASK = "duplicate_task"
    UNKNOWN_TOOL = "unknown_tool"
    INVALID_ARGUMENTS = "invalid_arguments"

class Recoverability(str, Enum):
    RECOVERABLE = "recoverable"
    FATAL = "fatal"

class PlanStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    FAILED = "failed"
    COMPLETED = "completed"

# ==========================
# Travel Framework Schemas
# ==========================

class TravelPreferences(BaseModel):
    hotel_rating: int | None = None
    flight_class: str | None = None
    dietary_preferences: list[str] = Field(default_factory=list)
    seat_preference: str | None = None
    hotel_facilities: list[str] = Field(default_factory=list)
    preferred_airlines: list[str] = Field(default_factory=list)
    hotel_brands: list[str] = Field(default_factory=list)

class TripConstraints(BaseModel):
    max_budget: float | None = None
    currency: str = "INR"
    max_layovers: int | None = None
    latest_arrival: str | None = None
    earliest_departure: str | None = None

class PlannerContext(BaseModel):
    destination: str | None = None
    preferences: TravelPreferences = Field(default_factory=TravelPreferences)
    constraints: TripConstraints = Field(default_factory=TripConstraints)
    conversation_summary: str = ""

class MemoryContext(BaseModel):
    retrieved_memories: list[str] = Field(default_factory=list)
    checkpoint_id: str | None = None

class MetadataContext(BaseModel):
    total_tokens: int = 0
    total_latency_ms: float = 0.0
    planner_calls: int = 0
    tool_calls: int = 0
    retry_count: int = 0
    graph_iterations: int = 0
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: datetime | None = None

# ==========================
# Run Logic & Interrupt Configuration
# ==========================



class InterruptState(BaseModel):
    type: str
    reason: str
    resume_token: str | None = None
    resume_context: dict = Field(default_factory=dict)

# ==========================
# Subgraph Output Boundary Results
# ==========================

class ValidationResult(BaseModel):
    valid: bool
    recoverable: Recoverability = Recoverability.RECOVERABLE
    error_type: ValidationErrorType | None = None
    message: str | None = None

class SchedulerResult(BaseModel):
    has_ready_tasks: bool = False
    ready_tasks: list[int] = Field(default_factory=list)
    waiting_tasks: list[int] = Field(default_factory=list)
    blocked_tasks: list[int] = Field(default_factory=list)
    failed_tasks: list[int] = Field(default_factory=list)
    completed_tasks: list[int] = Field(default_factory=list)

class ExecutorMetadata(BaseModel):
    latency_ms: float = 0.0
    provider: str | None = None
    tokens_used: int | None = None
    request_id: str | None = None

class ExecutorResult(BaseModel):
    success: bool
    output: Any = None
    error: str | None = None
    retryable: bool = False
    metadata: ExecutorMetadata = Field(default_factory=ExecutorMetadata)

class ExecutionPlan(BaseModel):
    plan_id: UUID = Field(default_factory=uuid4)
    tasks: dict[int, Task] = Field(default_factory=dict)
    version: int = 1
    parent_version: int | None = None
    planning_rationale: str | None = None
    planner_model: str | None = None
    plan_status: PlanStatus = PlanStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PlanningPipelineResult(BaseModel):
    execution_plan: ExecutionPlan
    validation_result: ValidationResult

class TaskExecutionResult(BaseModel):
    task: Task
    success: bool
    retryable: bool = False
    error: str | None = None
    executor_result: ExecutorResult | None = None

# ==========================
# Reducers
# ==========================

def merge_tasks(existing: dict[int, Task], updates: dict[int, Task]) -> dict[int, Task]:
    if existing is None:
        existing = {}
    if updates is None:
        return existing
    
    merged = dict(existing)
    for task_id, update_task in updates.items():
        if task_id in merged:
            # Merging in updates without losing attributes that might be omitted
            merged[task_id] = merged[task_id].model_copy(
                update=update_task.model_dump(exclude_unset=True)
            )
        else:
            merged[task_id] = update_task
    return merged

def merge_plans(existing: ExecutionPlan, new_updates: ExecutionPlan) -> ExecutionPlan:
    if existing is None:
        return new_updates
    if new_updates is None:
        return existing
        
    merged_tasks = merge_tasks(existing.tasks, new_updates.tasks)
    return existing.model_copy(update={
        "tasks": merged_tasks,
        "version": new_updates.version if new_updates.version is not None else existing.version,
        "parent_version": new_updates.parent_version if new_updates.parent_version is not None else existing.parent_version,
        "planning_rationale": new_updates.planning_rationale if new_updates.planning_rationale is not None else existing.planning_rationale,
        "planner_model": new_updates.planner_model if new_updates.planner_model is not None else existing.planner_model,
        "plan_status": new_updates.plan_status if new_updates.plan_status is not None else existing.plan_status,
    })

# ==========================
# State Classes
# ==========================

class TravelAgentState(TypedDict):
    # Persistent / Checkpointed Fields
    user_request: str
    messages: Annotated[list[AnyMessage], add_messages]
    execution_plan: Annotated[ExecutionPlan, merge_plans]
    replan_count: int
    planner_context: PlannerContext
    memory_context: MemoryContext
    
    # Runtime State Fields
    metadata_context: MetadataContext
    
    # Derived / Ephemeral Fields
    max_replan_attempts: int
    interrupt: InterruptState | None
    final_response: str
    validation_result: ValidationResult
    scheduler_result: SchedulerResult

# Rebuild Pydantic forward references for all schemas to guarantee runtime type resolution
TravelPreferences.model_rebuild()
TripConstraints.model_rebuild()
PlannerContext.model_rebuild()
MemoryContext.model_rebuild()
MetadataContext.model_rebuild()
InterruptState.model_rebuild()
ValidationResult.model_rebuild()
SchedulerResult.model_rebuild()
ExecutorMetadata.model_rebuild()
ExecutorResult.model_rebuild()
ExecutionPlan.model_rebuild()
PlanningPipelineResult.model_rebuild()
TaskExecutionResult.model_rebuild()
