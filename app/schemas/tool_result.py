from typing import Any
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """
    Standard envelope for all tool execution outputs across the application.
    """

    success: bool = Field(
        ...,
        description="Indicates whether the tool operation succeeded.",
    )
    data: Any = Field(
        default=None,
        description="Primary payload returned by the tool (dict, list, or primitive).",
    )
    error: str | None = Field(
        default=None,
        description="Detailed error message if the tool operation failed.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional execution metadata (timestamps, status codes, etc.).",
    )
