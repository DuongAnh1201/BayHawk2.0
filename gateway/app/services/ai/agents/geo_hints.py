"""Lightweight geographic hints for California-focused deployments (logging only)."""
from __future__ import annotations

import logging
from math import atan2, cos, radians, sin, sqrt
from typing import Any

logger = logging.getLogger(__name__)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two WGS84 points (kilometers)."""
    r_earth = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return r_earth * (2 * atan2(sqrt(a), sqrt(1 - a)))

# Approximate WGS84 bounds for California (mainland); not for legal jurisdiction.
_CA_LAT_S, _CA_LAT_N = 32.4, 42.1
_CA_LON_W, _CA_LON_E = -124.6, -114.0


def stage_location_metadata(
    lat: float,
    lon: float,
    *,
    bbox_wsen: str | None = None,
    focus_radius_km: float | None = None,
) -> dict[str, Any]:
    """Structured WGS84 context for agent ``raw`` / ``telemetry`` (focus uses ``focus_radius_km``)."""
    from app.config import settings

    r_km = float(settings.focus_radius_km if focus_radius_km is None else focus_radius_km)
    meta: dict[str, Any] = {
        "incident_lat": lat,
        "incident_lon": lon,
        "focus_radius_km": r_km,
        "focus_mode": "registered_cameras_within_radius_km",
    }
    if bbox_wsen is not None:
        meta["bbox_wsen"] = bbox_wsen
    return meta


def log_if_outside_california(lat: float, lon: float, *, context: str) -> None:
    """If coordinates are plausibly outside CA, log at INFO (pipeline still runs globally)."""
    if _CA_LAT_S <= lat <= _CA_LAT_N and _CA_LON_W <= lon <= _CA_LON_E:
        return
    logger.info("[%s] Coordinates outside typical California bbox (%.4f, %.4f); global APIs still used.", context, lat, lon)
