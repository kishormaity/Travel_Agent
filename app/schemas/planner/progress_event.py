from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.planner.task import TaskStatus


class ProgressEvent(BaseModel):
    """
    Represents a progress update event emitted during task execution.
    """

    task_id: int = Field(..., description="The ID of the task being executed.")
    description: str = Field(..., description="Human-readable description of the task.")
    tool_name: str = Field(..., description="Name of the tool being executed.")
    status: TaskStatus = Field(..., description="The status of the task at the time of the event.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the progress event.")
    execution_time: float | None = Field(default=None, description="Execution duration in seconds (if completed/failed/empty).")
    worker_id: int | None = Field(default=None, description="The ID of the worker thread executing this task.")
    retry_count: int = Field(default=0, description="The current retry count of the task.")
    error: str | None = Field(default=None, description="The error message if status is FAILED.")
