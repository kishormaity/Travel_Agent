import time
import threading
from typing import Any, Optional, Dict

class SimpleTTLCache:
    """Disabled Cache: Always returns None and performs no caching to ensure 100% real-time data."""
    def __init__(self, default_ttl_sec: float = 0.0):
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        return None

    def set(self, key: str, value: Any, ttl_sec: Optional[float] = None) -> None:
        pass

    def clear(self) -> None:
        pass

# Global singleton caches
weather_cache = SimpleTTLCache(default_ttl_sec=3600.0)      # 1 hour
places_cache = SimpleTTLCache(default_ttl_sec=7200.0)        # 2 hours
hotels_cache = SimpleTTLCache(default_ttl_sec=900.0)         # 15 minutes

