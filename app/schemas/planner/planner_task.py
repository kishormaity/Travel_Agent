from typing import Any

from pydantic import BaseModel, Field


class PlannerTask(BaseModel):
    """
    Represents a single task returned by the Planner LLM.

    This is NOT an execution task.
    It is simply the planner's proposed task.
    """

    description: str = Field(
        ...,
        description="Description of the task."
    )

    tool_name: str = Field(
        ...,
        description="Tool to execute."
    )

    arguments: dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments for the tool."
    )

    depends_on: list[int] = Field(
        default_factory=list,
        description="List of task IDs (1-indexed integers) this task depends on."
    )

    priority: int = Field(
        default=1,
        description="Priority of the task (lower is higher priority)."
    )