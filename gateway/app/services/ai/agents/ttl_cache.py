"""Small in-process TTL cache for repeated collection calls (cost / latency)."""
from __future__ import annotations

import asyncio
import time
from typing import Any


class AsyncTTLCache:
    def __init__(self, ttl_seconds: float) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        self.ttl_seconds = ttl_seconds
        self._data: dict[str, tuple[float, Any]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            row = self._data.get(key)
            if row is None:
                return None
            expires_at, val = row
            if time.monotonic() > expires_at:
                del self._data[key]
                return None
            return val

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._data[key] = (time.monotonic() + self.ttl_seconds, value)

    async def clear(self) -> None:
        async with self._lock:
            self._data.clear()
