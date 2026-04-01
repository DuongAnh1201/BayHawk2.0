"""Thermal wildfire hotspots via **NASA FIRMS** (global coverage, includes all of California).

Official API and map key registration:
  https://firms.modaps.eosdis.nasa.gov/api/area/

This agent calls the NASA FIRMS **Area API** JSON endpoint. The active product
layer is ``NASA_FIRMS_SOURCE`` (default ``VIIRS_SNPP_NRT``). Bounding box format is
``west,south,east,north`` in decimal degrees, per NASA Area API.
"""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import httpx
import logfire

from app.config import settings
from app.services.ai.schemas.pipeline import SatelliteResult

from .base import BaseAgent
from .collection_cache import get_named_cache
from .firms_area import (
    fetch_firms_area_json,
    firms_bbox_wsen,
    parse_hotspots,
    thermal_confidence_from_hotspots,
)
from .geo_hints import log_if_outside_california, stage_location_metadata

logger = logging.getLogger(__name__)


def _frp_value(hotspot: dict[str, Any]) -> float | None:
    """Backward-compatible name for tests; delegates to FIRMS parsing."""
    from .firms_area import frp_value

    return frp_value(hotspot)


def _satellite_cache_key(
    lat: float,
    lon: float,
    bbox_half: float,
    map_key: str,
    source: str,
    day_range: int,
) -> str:
    bbox = firms_bbox_wsen(lat, lon, bbox_half)
    raw = f"{bbox}|{map_key}|{source}|{day_range}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


class SatelliteAgent(BaseAgent):
    name = "satellite"

    def _telemetry_with_location(
        self,
        lat: float,
        lon: float,
        *,
        bbox_wsen: str | None,
        extra: dict[str, Any],
        focus_radius_km: float | None = None,
    ) -> dict[str, Any]:
        loc = stage_location_metadata(lat, lon, bbox_wsen=bbox_wsen, focus_radius_km=focus_radius_km)
        return {"location": loc, **extra}

    async def run(self, *, lat: float, lon: float, focus_radius_km: float | None = None, **_) -> SatelliteResult:
        fr_km = focus_radius_km if focus_radius_km is not None and focus_radius_km > 0 else None
        with logfire.span("agent.satellite", lat=lat, lon=lon, is_mock=settings.is_mock):
            t0 = time.perf_counter()
            if settings.is_mock:
                bbox_half = settings.firms_bbox_half_deg
                bbox_m = firms_bbox_wsen(lat, lon, bbox_half)
                result = SatelliteResult(
                    thermal_confidence=0.76,
                    hotspot_detected=True,
                    raw={
                        "hotspots": [{"frp": 76.0, "latitude": lat, "longitude": lon}],
                        "location": stage_location_metadata(lat, lon, bbox_wsen=bbox_m, focus_radius_km=fr_km),
                    },
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry=self._telemetry_with_location(
                        lat,
                        lon,
                        bbox_wsen=bbox_m,
                        focus_radius_km=fr_km,
                        extra={
                            "bbox_half_deg": bbox_half,
                            "firms_source": settings.nasa_firms_source,
                            "firms_area_day_range": settings.firms_area_day_range,
                        },
                    ),
                )
                logfire.info("satellite mock: thermal_confidence={tc}", tc=result.thermal_confidence)
                return result

            log_if_outside_california(lat, lon, context="satellite")
            bbox_half = settings.firms_bbox_half_deg
            max_attempts = settings.collection_http_max_attempts
            frp_norm = settings.firms_frp_normalize

            bbox = firms_bbox_wsen(lat, lon, bbox_half)

            if not (settings.nasa_firms_map_key or "").strip():
                logger.warning("NASA_FIRMS_MAP_KEY missing; satellite stage skipped")
                return SatelliteResult(
                    thermal_confidence=0.0,
                    hotspot_detected=False,
                    raw={
                        "error": "missing NASA_FIRMS_MAP_KEY",
                        "location": stage_location_metadata(lat, lon, bbox_wsen=bbox, focus_radius_km=fr_km),
                    },
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry=self._telemetry_with_location(
                        lat,
                        lon,
                        bbox_wsen=bbox,
                        focus_radius_km=fr_km,
                        extra={
                            "http_max_attempts": max_attempts,
                            "bbox_half_deg": bbox_half,
                            "frp_normalize": frp_norm,
                            "firms_source": settings.nasa_firms_source,
                            "firms_area_day_range": settings.firms_area_day_range,
                        },
                    ),
                )

            cache = get_named_cache("satellite_firms", settings.collection_cache_ttl_sec)
            ckey = _satellite_cache_key(
                lat,
                lon,
                bbox_half,
                settings.nasa_firms_map_key,
                settings.nasa_firms_source,
                settings.firms_area_day_range,
            )
            if cache is not None:
                cached = await cache.get(ckey)
                if cached is not None:
                    loc_meta = stage_location_metadata(lat, lon, bbox_wsen=bbox, focus_radius_km=fr_km)
                    merged_raw = dict(cached.raw or {})
                    merged_raw["location"] = loc_meta
                    return cached.model_copy(
                        deep=True,
                        update={
                            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                            "raw": merged_raw,
                            "telemetry": {
                                **(cached.telemetry or {}),
                                "location": loc_meta,
                                "cache_hit": True,
                                "api_calls_saved": 1,
                            },
                        },
                    )

            try:
                data = await fetch_firms_area_json(
                    bbox,
                    timeout=18.0,
                    max_attempts=max_attempts,
                    label="nasa_firms",
                )
            except httpx.HTTPError as exc:
                logger.warning("NASA FIRMS HTTP error: %s", exc)
                return SatelliteResult(
                    thermal_confidence=0.0,
                    hotspot_detected=False,
                    raw={
                        "error": str(exc),
                        "location": stage_location_metadata(lat, lon, bbox_wsen=bbox, focus_radius_km=fr_km),
                    },
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry=self._telemetry_with_location(
                        lat,
                        lon,
                        bbox_wsen=bbox,
                        focus_radius_km=fr_km,
                        extra={
                            "http_max_attempts": max_attempts,
                            "bbox_half_deg": bbox_half,
                            "firms_source": settings.nasa_firms_source,
                            "firms_area_day_range": settings.firms_area_day_range,
                        },
                    ),
                )
            except Exception as exc:
                logger.warning("NASA FIRMS request failed: %s", exc)
                return SatelliteResult(
                    thermal_confidence=0.0,
                    hotspot_detected=False,
                    raw={
                        "error": str(exc),
                        "location": stage_location_metadata(lat, lon, bbox_wsen=bbox, focus_radius_km=fr_km),
                    },
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry=self._telemetry_with_location(
                        lat,
                        lon,
                        bbox_wsen=bbox,
                        focus_radius_km=fr_km,
                        extra={
                            "http_max_attempts": max_attempts,
                            "bbox_half_deg": bbox_half,
                            "firms_source": settings.nasa_firms_source,
                            "firms_area_day_range": settings.firms_area_day_range,
                        },
                    ),
                )

            hotspots = parse_hotspots(data)
            thermal_confidence, hotspot_detected = thermal_confidence_from_hotspots(hotspots, frp_norm)

            logfire.info("satellite: hotspot={h} thermal_confidence={tc}", h=hotspot_detected, tc=thermal_confidence)
            result = SatelliteResult(
                thermal_confidence=thermal_confidence,
                hotspot_detected=hotspot_detected,
                raw={
                    "hotspots": hotspots,
                    "location": stage_location_metadata(lat, lon, bbox_wsen=bbox, focus_radius_km=fr_km),
                },
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                telemetry=self._telemetry_with_location(
                    lat,
                    lon,
                    bbox_wsen=bbox,
                    focus_radius_km=fr_km,
                    extra={
                        "http_max_attempts": max_attempts,
                        "bbox_half_deg": bbox_half,
                        "frp_normalize": frp_norm,
                        "cache_hit": False,
                        "firms_source": settings.nasa_firms_source,
                        "firms_area_day_range": settings.firms_area_day_range,
                    },
                ),
            )

            if cache is not None:
                await cache.set(ckey, result)

            return result
