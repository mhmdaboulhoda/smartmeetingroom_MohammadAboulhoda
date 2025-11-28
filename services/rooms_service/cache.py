"""Simple in-memory caching utilities for the rooms service."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Hashable, Optional, Tuple


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class RoomsCache:
    """Tiny TTL cache keyed by filter parameters.

    This keeps the implementation intentionally small so it can be documented
    in the Performance Optimization section of the project report.
    """

    def __init__(self, ttl_seconds: int = 60) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: Dict[Hashable, CacheEntry] = {}

    def _current_time(self) -> float:
        return time.monotonic()

    def _is_expired(self, entry: CacheEntry) -> bool:
        return self._current_time() >= entry.expires_at

    def make_key(
        self,
        location: Optional[str],
        min_capacity: Optional[int],
        status: Optional[str],
    ) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """Generate a hashable cache key from filters."""

        return (location, min_capacity, status)

    def get(self, key: Hashable) -> Optional[Any]:
        entry = self._store.get(key)
        if not entry:
            return None
        if self._is_expired(entry):
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: Hashable, value: Any) -> None:
        expires_at = self._current_time() + self.ttl_seconds
        self._store[key] = CacheEntry(value=value, expires_at=expires_at)

    def invalidate(self, predicate=None) -> None:
        """Invalidate cache entries. Predicate receives (key, entry)."""

        if predicate is None:
            self._store.clear()
            return
        keys_to_remove = [key for key, entry in self._store.items() if predicate(key, entry)]
        for key in keys_to_remove:
            self._store.pop(key, None)


rooms_cache = RoomsCache(ttl_seconds=60)
