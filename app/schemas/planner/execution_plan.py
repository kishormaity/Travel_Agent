from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

from app.schemas.planner.task import Task


class PlanStatus(str, Enum):
    """Execution plan lifecycle status."""
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    FAILED = "failed"
    COMPLETED = "completed"


class ExecutionPlan(BaseModel):
    """
    Authoritative container holding DAG tasks, version lineage, and global execution status.
    """
    plan_id: UUID = Field(default_factory=uuid4, description="Unique plan run identifier.")
    tasks: dict[int, Task] = Field(default_factory=dict, description="Task mapping keyed by sequential task ID.")
    version: int = Field(default=1, description="Plan version iteration (increments on replan).")
    parent_version: int | None = Field(default=None, description="Previous plan version if replanned.")
    planning_rationale: str | None = Field(default=None, description="Reasoning or notes for this plan version.")
    planner_model: str | None = Field(default=None, description="LLM model used to generate this plan.")
    plan_status: PlanStatus = Field(default=PlanStatus.ACTIVE, description="Current lifecycle state of the plan.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when plan was generated.")