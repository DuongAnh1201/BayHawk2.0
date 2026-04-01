from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CameraCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    image_url: str = Field(..., min_length=1, description="HTTP(S) snapshot URL for YOLO")


class CameraRead(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    image_url: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CameraUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)
    image_url: str | None = Field(None, min_length=1)
    is_active: bool | None = None
