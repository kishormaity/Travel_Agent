from pydantic import BaseModel, Field

class RetryPolicy(BaseModel):
    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    jitter_min: float = 0.1
    jitter_max: float = 0.5
