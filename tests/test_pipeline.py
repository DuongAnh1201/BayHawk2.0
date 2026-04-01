"""
Full pipeline mock tests.

Run with:
    IS_MOCK=true pytest tests/ -v
"""
import pytest
from unittest.mock import AsyncMock, patch

from app.services.ai.agents.orchestrator import OrchestratorAgent
from app.services.ai.agents.camera import CameraAgent
from app.services.ai.agents.satellite import SatelliteAgent
from app.services.ai.agents.weather import WeatherAgent
from app.services.ai.agents.reasoning import ReasoningAgent
from app.services.ai.agents.classification import ClassificationAgent
from app.services.ai.agents.suggestion import SuggestionAgent
from app.services.ai.agents.output import OutputAgent
from app.services.ai.schemas.pipeline import ConfirmationStatus, CriticalityLevel


# ── Helpers ────────────────────────────────────────────────────────────────────

def _patch_all_confirmed(
    camera_confirmed,
    satellite_confirmed,
    weather_result,
    reasoning_result,
    classification_result,
    suggestion_result,
    output_result,
):
    """Context manager that patches every agent with CONFIRMED-path mock data."""
    return (
        patch.object(CameraAgent, "run", new=AsyncMock(return_value=camera_confirmed)),
        patch.object(SatelliteAgent, "run", new=AsyncMock(return_value=satellite_confirmed)),
        patch.object(WeatherAgent, "run", new=AsyncMock(return_value=weather_result)),
        patch.object(ReasoningAgent, "run", new=AsyncMock(return_value=reasoning_result)),
        patch.object(ClassificationAgent, "run", new=AsyncMock(return_value=classification_result)),
        patch.object(SuggestionAgent, "run", new=AsyncMock(return_value=suggestion_result)),
        patch.object(OutputAgent, "run", new=AsyncMock(return_value=output_result)),
    )


# ── Tests ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_confirmed_full(
    alert_event,
    camera_confirmed,
    satellite_confirmed,
    weather_result,
    reasoning_result,
    classification_result,
    suggestion_result,
    output_result,
):
    """
    CONFIRMED path: all stages run, PipelineResult is fully populated.
    FusionAgent runs on real logic (no patch) to verify the score calculation.
    """
    patches = _patch_all_confirmed(
        camera_confirmed, satellite_confirmed, weather_result,
        reasoning_result, classification_result, suggestion_result, output_result,
    )
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        orchestrator = OrchestratorAgent()
        result = await orchestrator.run(event=alert_event)

    # Stage 1
    assert result.camera.detected is True
    assert result.satellite.hotspot_detected is True
    assert result.weather.spread_risk > 0

    # Stage 2 – real fusion logic
    assert result.fusion.status == ConfirmationStatus.CONFIRMED
    assert result.fusion.combined_score == pytest.approx(
        camera_confirmed.confidence * 0.6 + satellite_confirmed.thermal_confidence * 0.4,
        abs=1e-4,
    )

    # Stage 3–6
    assert result.reasoning is not None
    assert result.classification.criticality == CriticalityLevel.HIGH
    assert len(result.suggestion.action_plan) > 0
    assert result.output.logged is True
    assert result.error is None


@pytest.mark.asyncio
async def test_pipeline_dismissed_stops_after_fusion(
    alert_event,
    camera_dismissed,
    satellite_dismissed,
    weather_result,
):
    """
    DISMISSED path: pipeline stops after fusion; stages 3–6 must NOT be called.
    """
    reasoning_mock = AsyncMock()
    classification_mock = AsyncMock()
    suggestion_mock = AsyncMock()
    output_mock = AsyncMock()

    with (
        patch.object(CameraAgent, "run", new=AsyncMock(return_value=camera_dismissed)),
        patch.object(SatelliteAgent, "run", new=AsyncMock(return_value=satellite_dismissed)),
        patch.object(WeatherAgent, "run", new=AsyncMock(return_value=weather_result)),
        patch.object(ReasoningAgent, "run", new=reasoning_mock),
        patch.object(ClassificationAgent, "run", new=classification_mock),
        patch.object(SuggestionAgent, "run", new=suggestion_mock),
        patch.object(OutputAgent, "run", new=output_mock),
    ):
        orchestrator = OrchestratorAgent()
        result = await orchestrator.run(event=alert_event)

    assert result.fusion.status == ConfirmationStatus.DISMISSED
    assert result.reasoning is None
    assert result.classification is None
    assert result.suggestion is None
    assert result.output is None

    reasoning_mock.assert_not_called()
    classification_mock.assert_not_called()
    suggestion_mock.assert_not_called()
    output_mock.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_is_mock_flag(alert_event):
    """
    With IS_MOCK=true every agent returns its hardcoded mock data —
    no HTTP calls or LLM calls are made.
    """
    import app.config as cfg_module

    original = cfg_module.settings.is_mock
    try:
        cfg_module.settings.is_mock = True
        orchestrator = OrchestratorAgent()
        result = await orchestrator.run(event=alert_event)
    finally:
        cfg_module.settings.is_mock = original

    assert result.fusion.status == ConfirmationStatus.CONFIRMED
    assert result.reasoning.scene_description != ""
    assert result.classification.criticality in list(CriticalityLevel)
    assert result.suggestion.alert_message != ""
    assert result.output.logged is True
    # In mock mode the webhook is skipped
    assert result.output.notification_sent is False


@pytest.mark.asyncio
async def test_fusion_score_boundary():
    """
    Unit test: fusion threshold logic.
    Score exactly at threshold (0.40) → CONFIRMED.
    Score just below (0.39) + no both_positive → DISMISSED.
    """
    from app.services.ai.agents.fusion import FusionAgent
    from app.services.ai.schemas.pipeline import CameraResult, SatelliteResult

    agent = FusionAgent()

    # Exactly at threshold: 0.40*0.6 + 0.40*0.4 = 0.40 → CONFIRMED
    at_threshold = await agent.run(
        camera=CameraResult(confidence=0.40, detected=False),
        satellite=SatelliteResult(thermal_confidence=0.40, hotspot_detected=False),
    )
    assert at_threshold.status == ConfirmationStatus.CONFIRMED

    # Just below: 0.30*0.6 + 0.20*0.4 = 0.26 → DISMISSED
    below = await agent.run(
        camera=CameraResult(confidence=0.30, detected=False),
        satellite=SatelliteResult(thermal_confidence=0.20, hotspot_detected=False),
    )
    assert below.status == ConfirmationStatus.DISMISSED

    # Both detectors positive → CONFIRMED regardless of score
    both_positive = await agent.run(
        camera=CameraResult(confidence=0.05, detected=True),
        satellite=SatelliteResult(thermal_confidence=0.05, hotspot_detected=True),
    )
    assert both_positive.status == ConfirmationStatus.CONFIRMED


@pytest.mark.asyncio
async def test_weather_spread_risk_calculation():
    """Unit test: spread risk heuristic produces values in [0, 1]."""
    from app.services.ai.agents.weather import WeatherAgent
    import app.config as cfg_module

    original = cfg_module.settings.is_mock
    try:
        cfg_module.settings.is_mock = True
        agent = WeatherAgent()
        result = await agent.run(lat=34.0, lon=-118.0)
    finally:
        cfg_module.settings.is_mock = original

    assert 0.0 <= result.spread_risk <= 1.0
    assert result.wind_speed >= 0
    assert 0.0 <= result.humidity <= 100.0


@pytest.mark.asyncio
async def test_pipeline_event_id_propagation(alert_event):
    """PipelineResult.event_id must match the input AlertEvent.event_id."""
    import app.config as cfg_module

    original = cfg_module.settings.is_mock
    try:
        cfg_module.settings.is_mock = True
        result = await OrchestratorAgent().run(event=alert_event)
    finally:
        cfg_module.settings.is_mock = original

    assert result.event_id == alert_event.event_id
