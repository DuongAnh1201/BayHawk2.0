"""Lightweight geographic hints for California-focused deployments (logging only)."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Approximate WGS84 bounds for California (mainland); not for legal jurisdiction.
_CA_LAT_S, _CA_LAT_N = 32.4, 42.1
_CA_LON_W, _CA_LON_E = -124.6, -114.0


def log_if_outside_california(lat: float, lon: float, *, context: str) -> None:
    """If coordinates are plausibly outside CA, log at INFO (pipeline still runs globally)."""
    if _CA_LAT_S <= lat <= _CA_LAT_N and _CA_LON_W <= lon <= _CA_LON_E:
        return
    logger.info("[%s] Coordinates outside typical California bbox (%.4f, %.4f); global APIs still used.", context, lat, lon)
