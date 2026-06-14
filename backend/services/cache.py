import hashlib
import json
import time
from typing import Any, Optional

from models import JobFilter


class CacheManager:
    """In-memory cache with TTL support and optional JSON file backup."""

    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if it exists and has not expired."""
        entry = self._cache.get(key)
        if entry is None:
            return None

        if time.time() > entry["expiry"]:
            del self._cache[key]
            return None

        return entry["value"]

    def set(self, key: str, value: Any, ttl_minutes: int = 30) -> None:
        """Store a value in the cache with an expiry timestamp."""
        self._cache[key] = {
            "value": value,
            "expiry": time.time() + (ttl_minutes * 60),
        }

    def make_key(self, filters: JobFilter) -> str:
        """Create a deterministic hash key from filter parameters."""
        filter_dict = filters.model_dump()
        # Sort for deterministic ordering
        filter_str = json.dumps(filter_dict, sort_keys=True)
        return hashlib.sha256(filter_str.encode()).hexdigest()

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
