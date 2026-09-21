import random
import httpx
from pydantic import BaseModel, Field, ValidationError


class RetryPolicy(BaseModel):
    """
    Resilience policy for task execution retries, exponential backoff, jitter,
    and concrete exception classification.
    """
    max_attempts: int = Field(default=3, description="Maximum execution attempts (1 initial + 2 retries).")
    initial_delay: float = Field(default=1.0, description="Initial backoff delay in seconds.")
    backoff_factor: float = Field(default=2.0, description="Exponential backoff multiplier.")
    max_delay: float = Field(default=10.0, description="Maximum backoff delay ceiling in seconds.")
    jitter_min: float = Field(default=0.1, description="Minimum uniform jitter in seconds.")
    jitter_max: float = Field(default=0.5, description="Maximum uniform jitter in seconds.")

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate backoff delay for the given attempt index (1-indexed).
        Applies exponential backoff capped at max_delay, plus jitter.
        """
        raw_delay = self.initial_delay * (self.backoff_factor ** max(0, attempt - 1))
        capped_delay = min(self.max_delay, raw_delay)
        jitter = random.uniform(self.jitter_min, self.jitter_max)
        return round(capped_delay + jitter, 3)

    def is_retryable(self, exception: Exception | None) -> bool:
        """
        Classifies an exception as transient/retryable vs. permanent.
        Inspects concrete exception types and unwraps chained causes.
        """
        if exception is None:
            return False

        # Unwind chained exceptions to find root cause if wrapped
        candidates = [exception]
        curr = exception
        while curr.__cause__ is not None or curr.__context__ is not None:
            curr = curr.__cause__ or curr.__context__
            if curr not in candidates:
                candidates.append(curr)

        for exc in candidates:
            # 1. Concrete permanent errors (explicit fast-fail)
            if isinstance(exc, (ValidationError, ValueError, TypeError, KeyError)):
                return False

            if isinstance(exc, httpx.HTTPStatusError):
                status = exc.response.status_code if exc.response is not None else None
                if status is not None:
                    if status == 429:
                        return True
                    if 500 <= status < 600:
                        return True
                    if 400 <= status < 500:
                        return False

            # 2. Concrete transient network/transport errors
            if isinstance(exc, (httpx.TimeoutException, httpx.NetworkError, httpx.RequestError)):
                return True

            if isinstance(exc, (ConnectionError, TimeoutError)):
                return True

        return False

