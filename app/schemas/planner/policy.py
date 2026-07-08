from enum import Enum


class ExecutionPolicy(str, Enum):
    """
    Determines execution behavior when a task fails or returns an empty result.
    """

    FAIL_FAST = "fail_fast"
    CONTINUE = "continue"
    BEST_EFFORT = "best_effort"
