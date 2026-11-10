import time
import threading
from typing import Any, Optional, Dict

class SimpleTTLCache:
    """Thread-safe in-memory cache with expiration timestamps to eliminate redundant network roundtrips."""
    def __init__(self, default_ttl_sec: float = 3600.0):
        self._store: Dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self._default_ttl = default_ttl_sec
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._store:
                expiry, val = self._store[key]
                if time.time() < expiry:
                    self.hits += 1
                    return val
                else:
                    del self._store[key]
            self.misses += 1
            return None

    def set(self, key: str, value: Any, ttl_sec: Optional[float] = None) -> None:
        ttl = ttl_sec if ttl_sec is not None else self._default_ttl
        with self._lock:
            self._store[key] = (time.time() + ttl, value)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

# Global singleton caches
weather_cache = SimpleTTLCache(default_ttl_sec=3600.0)      # 1 hour
places_cache = SimpleTTLCache(default_ttl_sec=7200.0)        # 2 hours
hotels_cache = SimpleTTLCache(default_ttl_sec=900.0)         # 15 minutes
