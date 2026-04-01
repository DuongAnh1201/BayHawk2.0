"""Shared fixtures for the BayHawk pipeline test suite."""
import pytest

from app.services.ai.schemas.pipeline import (
    AlertEvent,
    CameraResult,
    ClassificationResult,
    ConfirmationStatus,
    CriticalityLevel,
    FusionResult,
    OutputResult,
    ReasoningResult,
    SatelliteResult,
    SuggestionResult,
    WeatherResult,
)


# ── Event ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def alert_event() -> AlertEvent:
    return AlertEvent(
        event_id="test-event-001",
        lat=34.0522,
        lon=-118.2437,
        camera_id="cam-ridge-001",
        image_url="https://mock.alertcalifornia.org/cam001.jpg",
        timestamp="2026-04-01T12:00:00Z",
    )


# ── Stage results (CONFIRMED path) ────────────────────────────────────────────

@pytest.fixture
def camera_confirmed() -> CameraResult:
    return CameraResult(
        confidence=0.87,
        detected=True,
        image_url="https://mock.alertcalifornia.org/cam001.jpg",
        raw={"cameras": [{"id": "cam-ridge-001"}]},
    )


@pytest.fixture
def satellite_confirmed() -> SatelliteResult:
    return SatelliteResult(
        thermal_confidence=0.76,
        hotspot_detected=True,
        raw={"hotspots": [{"frp": 76.0, "latitude": 34.05, "longitude": -118.24}]},
    )


@pytest.fixture
def weather_result() -> WeatherResult:
    return WeatherResult(
        wind_speed=13.5,
        wind_direction=225.0,
        humidity=18.0,
        spread_risk=0.74,
        raw={"wind": {"speed": 13.5, "deg": 225}, "main": {"humidity": 18}},
    )


@pytest.fixture
def fusion_confirmed() -> FusionResult:
    return FusionResult(
        status=ConfirmationStatus.CONFIRMED,
        combined_score=0.83,
        reason="Combined score 0.83 meets threshold.",
    )


@pytest.fixture
def reasoning_result() -> ReasoningResult:
    return ReasoningResult(
        scene_description="Active flame front advancing northeast through dry chaparral.",
        key_observations=[
            "Flame front moving northeast",
            "Dry chaparral as primary fuel",
            "Structures 1.2 km from perimeter",
        ],
    )


@pytest.fixture
def classification_result() -> ClassificationResult:
    return ClassificationResult(
        criticality=CriticalityLevel.HIGH,
        score=0.82,
        reasoning="High wind speed and low humidity drive rapid spread.",
    )


@pytest.fixture
def suggestion_result() -> SuggestionResult:
    return SuggestionResult(
        action_plan=["Deploy aerial tankers", "Issue evacuation order for Zone A"],
        alert_message="WILDFIRE ALERT – HIGH criticality. Evacuate Zone A immediately.",
        recommended_resources=["2× aerial tankers", "4× Type-1 engine crews"],
    )


@pytest.fixture
def output_result() -> OutputResult:
    return OutputResult(
        notification_sent=False,
        dashboard_updated=False,
        incident_id="mock-incident-001",
        logged=True,
    )


# ── Stage results (DISMISSED path) ────────────────────────────────────────────

@pytest.fixture
def camera_dismissed() -> CameraResult:
    return CameraResult(confidence=0.05, detected=False, image_url=None, raw={})


@pytest.fixture
def satellite_dismissed() -> SatelliteResult:
    return SatelliteResult(thermal_confidence=0.03, hotspot_detected=False, raw={"hotspots": []})


@pytest.fixture
def fusion_dismissed() -> FusionResult:
    return FusionResult(
        status=ConfirmationStatus.DISMISSED,
        combined_score=0.04,
        reason="Combined score 0.04 below threshold 0.40.",
    )
