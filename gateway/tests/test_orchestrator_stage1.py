"""Orchestrator stage-1 resilience when an agent raises."""

from __future__ import annotations

import pytest

from app.services.ai.agents.orchestrator import OrchestratorAgent
from app.services.ai.schemas.pipeline import (
    AlertEvent,
    ConfirmationStatus,
    FusionResult,
    SatelliteResult,
    WeatherResult,
)


@pytest.mark.asyncio
async def test_stage1_camera_exception_still_returns_pipeline(monkeypatch):
    orch = OrchestratorAgent()

    async def camera_raises(**_kwargs):
        raise RuntimeError("simulated camera failure")

    async def satellite_ok(**_kwargs):
        return SatelliteResult(thermal_confidence=0.0, hotspot_detected=False, raw={})

    async def weather_ok(**_kwargs):
        return WeatherResult(
            wind_speed=0.0, wind_direction=0.0, humidity=50.0, spread_risk=0.2, raw={}
        )

    async def fusion_early_stop(**_kwargs):
        return FusionResult(status=ConfirmationStatus.DISMISSED, combined_score=0.0, reason="test")

    monkeypatch.setattr(orch.camera, "run", camera_raises)
    monkeypatch.setattr(orch.satellite, "run", satellite_ok)
    monkeypatch.setattr(orch.weather, "run", weather_ok)
    monkeypatch.setattr(orch.fusion, "run", fusion_early_stop)

    event = AlertEvent(
        event_id="e-resilience",
        lat=37.77,
        lon=-122.42,
        timestamp="2026-04-01T12:00:00Z",
    )
    result = await orch.run(event=event)

    assert result.camera is not None
    assert result.camera.raw.get("error") == "agent_exception"
    assert "simulated camera failure" in (result.camera.raw.get("detail") or "")
    assert result.fusion is not None
    assert result.fusion.status == ConfirmationStatus.DISMISSED
