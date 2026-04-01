"""Thermal wildfire hotspots via **NASA FIRMS** (global coverage, includes all of California).

Official API and map key registration:
  https://firms.modaps.eosdis.nasa.gov/api/area/

This agent uses the **VIIRS_SNPP_NRT** layer (Suomi NPP, near real-time). Bounding
box format is ``west,south,east,north`` in decimal degrees, per NASA Area API.
California falls entirely within valid bounds for this product.
"""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.services.ai.schemas.pipeline import SatelliteResult

from .base import BaseAgent
from .collection_cache import get_named_cache
from .geo_hints import log_if_outside_california
from .http_retry import httpx_get_json

logger = logging.getLogger(__name__)


def _frp_value(hotspot: dict[str, Any]) -> float | None:
    raw = hotspot.get("frp")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _satellite_cache_key(lat: float, lon: float, bbox_half: float, map_key: str) -> str:
    west, south, east, north = lon - bbox_half, lat - bbox_half, lon + bbox_half, lat + bbox_half
    raw = f"{west:.5f},{south:.5f},{east:.5f},{north:.5f}|{map_key}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class SatelliteAgent(BaseAgent):
    name = "satellite"

    async def run(self, *, lat: float, lon: float, **_) -> SatelliteResult:
        t0 = time.perf_counter()
        log_if_outside_california(lat, lon, context="satellite")
        bbox_half = settings.firms_bbox_half_deg
        max_attempts = settings.collection_http_max_attempts
        frp_norm = settings.firms_frp_normalize

        if not (settings.nasa_firms_map_key or "").strip():
            logger.warning("NASA_FIRMS_MAP_KEY missing; satellite stage skipped")
            return SatelliteResult(
                thermal_confidence=0.0,
                hotspot_detected=False,
                raw={"error": "missing NASA_FIRMS_MAP_KEY"},
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                telemetry={
                    "http_max_attempts": max_attempts,
                    "bbox_half_deg": bbox_half,
                    "frp_normalize": frp_norm,
                },
            )

        cache = get_named_cache("satellite_firms", settings.collection_cache_ttl_sec)
        ckey = _satellite_cache_key(lat, lon, bbox_half, settings.nasa_firms_map_key)
        if cache is not None:
            cached = await cache.get(ckey)
            if cached is not None:
                return cached.model_copy(
                    deep=True,
                    update={
                        "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                        "telemetry": {
                            **(cached.telemetry or {}),
                            "cache_hit": True,
                            "api_calls_saved": 1,
                        },
                    },
                )

        west, south, east, north = lon - bbox_half, lat - bbox_half, lon + bbox_half, lat + bbox_half
        bbox = f"{west},{south},{east},{north}"
        url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/json/"
            f"{settings.nasa_firms_map_key}/VIIRS_SNPP_NRT/{bbox}/1"
        )

        try:
            data = await httpx_get_json(url, timeout=18.0, max_attempts=max_attempts, label="nasa_firms")
        except httpx.HTTPError as exc:
            logger.warning("NASA FIRMS HTTP error: %s", exc)
            return SatelliteResult(
                thermal_confidence=0.0,
                hotspot_detected=False,
                raw={"error": str(exc)},
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                telemetry={"http_max_attempts": max_attempts, "bbox_half_deg": bbox_half},
            )
        except Exception as exc:  # pragma: no cover - JSON/defensive
            logger.warning("NASA FIRMS request failed: %s", exc)
            return SatelliteResult(
                thermal_confidence=0.0,
                hotspot_detected=False,
                raw={"error": str(exc)},
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                telemetry={"http_max_attempts": max_attempts, "bbox_half_deg": bbox_half},
            )

        hotspots = data if isinstance(data, list) else data.get("data", [])
        if not isinstance(hotspots, list):
            hotspots = []
        hotspot_detected = len(hotspots) > 0
        thermal_confidence = 0.0

        if hotspot_detected:
            frp_values: list[float] = []
            for h in hotspots:
                if isinstance(h, dict):
                    v = _frp_value(h)
                    if v is not None:
                        frp_values.append(v)
            if frp_values:
                thermal_confidence = min(max(frp_values) / frp_norm, 1.0)

        result = SatelliteResult(
            thermal_confidence=thermal_confidence,
            hotspot_detected=hotspot_detected,
            raw={"hotspots": hotspots},
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            telemetry={
                "http_max_attempts": max_attempts,
                "bbox_half_deg": bbox_half,
                "frp_normalize": frp_norm,
                "cache_hit": False,
            },
        )

        if cache is not None:
            await cache.set(ckey, result)

        return result
