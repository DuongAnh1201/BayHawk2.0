"""Fusion accuracy tradeoffs (threshold + weights) from settings."""

from __future__ import annotations

import pytest

from app.config import settings
from app.services.ai.agents.fusion import FusionAgent
from app.services.ai.schemas.pipeline import CameraResult, ConfirmationStatus, SatelliteResult


@pytest.mark.asyncio
async def test_fusion_telemetry_includes_weights(monkeypatch):
    monkeypatch.setattr(settings, "fusion_threshold", 0.4)
    monkeypatch.setattr(settings, "fusion_camera_weight", 0.6)
    camera = CameraResult(confidence=0.5, detected=False, raw={})
    sat = SatelliteResult(thermal_confidence=0.5, hotspot_detected=False, raw={})
    out = await FusionAgent().run(camera=camera, satellite=sat)
    assert out.telemetry["weight_camera"] == pytest.approx(0.6)
    assert out.telemetry["weight_thermal"] == pytest.approx(0.4)
    assert out.telemetry["fusion_threshold"] == pytest.approx(0.4)


@pytest.mark.asyncio
async def test_high_threshold_dismisses_without_both_positive(monkeypatch):
    monkeypatch.setattr(settings, "fusion_threshold", 0.99)
    monkeypatch.setattr(settings, "fusion_camera_weight", 0.5)
    camera = CameraResult(confidence=0.9, detected=True, raw={})
    sat = SatelliteResult(thermal_confidence=0.9, hotspot_detected=False, raw={})
    out = await FusionAgent().run(camera=camera, satellite=sat)
    assert out.status == ConfirmationStatus.DISMISSED


@pytest.mark.asyncio
async def test_both_positive_overrides_high_threshold(monkeypatch):
    monkeypatch.setattr(settings, "fusion_threshold", 0.99)
    monkeypatch.setattr(settings, "fusion_camera_weight", 0.5)
    camera = CameraResult(confidence=0.2, detected=True, raw={})
    sat = SatelliteResult(thermal_confidence=0.2, hotspot_detected=True, raw={})
    out = await FusionAgent().run(camera=camera, satellite=sat)
    assert out.status == ConfirmationStatus.CONFIRMED
    assert out.telemetry["both_positive_override"] is True
