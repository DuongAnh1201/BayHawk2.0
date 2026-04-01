"""Named TTL caches for weather / satellite (optional via COLLECTION_CACHE_TTL_SEC)."""
from __future__ import annotations

from app.services.ai.agents.ttl_cache import AsyncTTLCache

_registry: dict[str, AsyncTTLCache] = {}


def get_named_cache(scope: str, ttl_sec: int) -> AsyncTTLCache | None:
    if ttl_sec <= 0:
        return None
    cached = _registry.get(scope)
    if cached is None or abs(cached.ttl_seconds - ttl_sec) > 1e-6:
        cached = AsyncTTLCache(float(ttl_sec))
        _registry[scope] = cached
    return cached


def clear_all_collection_caches() -> None:
    """For tests or hot-reload; drops cache instances."""
    _registry.clear()
