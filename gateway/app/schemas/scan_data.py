from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.cameras import CameraRead


class ScanResultRead(BaseModel):
    id: int
    camera_id: int
    confidence: float
    detected: bool
    scan_type: str
    observed_lat: float | None
    observed_lon: float | None
    snapshot_url: str | None
    scan_metadata: dict[str, Any]
    created_at: datetime
    camera: CameraRead | None = None

    model_config = {"from_attributes": True}


class SatelliteObservationRead(BaseModel):
    id: int
    lat: float
    lon: float
    frp: float | None
    raw: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


def clamp_limit(limit: int, *, max_value: int = 200) -> int:
    return max(1, min(limit, max_value))
