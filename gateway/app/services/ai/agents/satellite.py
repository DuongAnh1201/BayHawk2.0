"""Thermal wildfire hotspots via **NASA FIRMS** (global coverage, includes all of California).

Official API and map key registration:
  https://firms.modaps.eosdis.nasa.gov/api/area/

This agent uses the **VIIRS_SNPP_NRT** layer (Suomi NPP, near real-time). Bounding
box format is ``west,south,east,north`` in decimal degrees, per NASA Area API.
California falls entirely within valid bounds for this product.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.services.ai.schemas.pipeline import SatelliteResult

from .base import BaseAgent
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


class SatelliteAgent(BaseAgent):
    name = "satellite"

    async def run(self, *, lat: float, lon: float, **_) -> SatelliteResult:
        t0 = time.perf_counter()
        if settings.is_mock:
            return SatelliteResult(
                thermal_confidence=0.76,
                hotspot_detected=True,
                raw={"hotspots": [{"frp": 76.0, "latitude": lat, "longitude": lon}]},
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                telemetry={"bbox_half_deg": 0.1},
            )
        # NASA FIRMS – active fire / hotspot data (VIIRS SNPP Near-Real-Time)
        bbox_half = 0.1
        max_attempts = settings.collection_http_max_attempts
        frp_norm = settings.firms_frp_normalize
        bbox = f"{lon - bbox_half},{lat - bbox_half},{lon + bbox_half},{lat + bbox_half}"
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

        return SatelliteResult(
            thermal_confidence=thermal_confidence,
            hotspot_detected=hotspot_detected,
            raw={"hotspots": hotspots},
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            telemetry={
                "http_max_attempts": max_attempts,
                "bbox_half_deg": bbox_half,
                "frp_normalize": frp_norm,
            },
        )
