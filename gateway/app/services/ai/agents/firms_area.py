"""NASA FIRMS Area API (JSON) — shared fetch and hotspot scoring for camera + satellite agents."""
from __future__ import annotations

from typing import Any

from app.config import settings

from .http_retry import httpx_get_json


def firms_bbox_wsen(lat: float, lon: float, half_deg: float) -> str:
    west, south, east, north = lon - half_deg, lat - half_deg, lon + half_deg, lat + half_deg
    return f"{west},{south},{east},{north}"


def firms_area_url(bbox: str) -> str:
    key = (settings.nasa_firms_map_key or "").strip()
    return (
        f"https://firms.modaps.eosdis.nasa.gov/api/area/json/"
        f"{key}/{settings.nasa_firms_source}/{bbox}/{settings.firms_area_day_range}"
    )


async def fetch_firms_area_json(
    bbox: str,
    *,
    timeout: float,
    max_attempts: int,
    label: str,
) -> Any:
    return await httpx_get_json(
        firms_area_url(bbox),
        timeout=timeout,
        max_attempts=max_attempts,
        label=label,
    )


def frp_value(hotspot: dict[str, Any]) -> float | None:
    raw = hotspot.get("frp")
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def parse_hotspots(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        hotspots = data.get("data", [])
        return hotspots if isinstance(hotspots, list) else []
    return []


def thermal_confidence_from_hotspots(hotspots: list[Any], frp_norm: float) -> tuple[float, bool]:
    """Return (thermal_confidence in [0,1], any_hotspot_present). Matches satellite scoring."""
    hotspot_detected = len(hotspots) > 0
    thermal_confidence = 0.0
    if hotspot_detected:
        frp_values: list[float] = []
        for h in hotspots:
            if isinstance(h, dict):
                v = frp_value(h)
                if v is not None:
                    frp_values.append(v)
        if frp_values:
            thermal_confidence = min(max(frp_values) / frp_norm, 1.0)
    return thermal_confidence, hotspot_detected
