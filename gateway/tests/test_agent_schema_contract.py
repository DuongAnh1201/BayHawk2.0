"""Assert Camera, Satellite, and Weather agents return full pipeline schema contracts.

These tests mock HTTP so they run in CI without API keys. They validate:
  • Pydantic models parse and round-trip (``model_validate(model_dump())``)
  • Required fields exist with correct types
  • Semantic bounds (e.g. confidences in [0, 1])
  • ``raw`` / ``telemetry`` / ``latency_ms`` shapes when applicable
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.ai.agents.camera import CameraAgent
from app.services.ai.agents.satellite import SatelliteAgent
from app.services.ai.agents.weather import WeatherAgent
from app.services.ai.schemas.pipeline import CameraResult, SatelliteResult, WeatherResult


def _assert_camera_contract(r: CameraResult) -> None:
    CameraResult.model_validate(r.model_dump())
    assert isinstance(r.confidence, float)
    assert isinstance(r.detected, bool)
    assert 0.0 <= r.confidence <= 1.0
    assert r.image_url is None or isinstance(r.image_url, str)
    assert r.raw is None or isinstance(r.raw, dict)
    assert r.latency_ms is None or isinstance(r.latency_ms, (int, float))
    assert r.latency_ms is None or r.latency_ms >= 0.0
    assert r.telemetry is None or isinstance(r.telemetry, dict)
    if r.telemetry:
        assert "http_max_attempts" in r.telemetry
        assert "yolo_imgsz" in r.telemetry


def _assert_satellite_contract(r: SatelliteResult) -> None:
    SatelliteResult.model_validate(r.model_dump())
    assert isinstance(r.thermal_confidence, float)
    assert isinstance(r.hotspot_detected, bool)
    assert 0.0 <= r.thermal_confidence <= 1.0
    assert r.raw is None or isinstance(r.raw, dict)
    assert r.latency_ms is None or (isinstance(r.latency_ms, (int, float)) and r.latency_ms >= 0.0)
    assert r.telemetry is None or isinstance(r.telemetry, dict)
    if r.hotspot_detected and r.raw and "hotspots" in r.raw:
        assert isinstance(r.raw["hotspots"], list)


def _assert_weather_contract(r: WeatherResult) -> None:
    WeatherResult.model_validate(r.model_dump())
    assert isinstance(r.wind_speed, float)
    assert isinstance(r.wind_direction, float)
    assert isinstance(r.humidity, float)
    assert isinstance(r.spread_risk, float)
    assert 0.0 <= r.humidity <= 100.0
    assert 0.0 <= r.spread_risk <= 1.0
    assert r.wind_speed >= 0.0
    assert 0.0 <= r.wind_direction <= 360.0
    assert r.raw is None or isinstance(r.raw, dict)
    assert r.latency_ms is None or (isinstance(r.latency_ms, (int, float)) and r.latency_ms >= 0.0)
    assert r.telemetry is None or isinstance(r.telemetry, dict)


# --- Camera -----------------------------------------------------------------


@pytest.mark.asyncio
async def test_camera_schema_success_with_alertca_and_yolo():
    alert_payload = {"cameras": [{"image_url": "https://example.com/still.jpg"}]}
    with (
        patch(
            "app.services.ai.agents.camera.httpx_get_json",
            new_callable=AsyncMock,
            return_value=alert_payload,
        ),
        patch.object(CameraAgent, "_run_yolo", new_callable=AsyncMock, return_value=(0.73, True)),
        patch("app.services.ai.agents.camera.settings.alertca_api_key", "token"),
    ):
        r = await CameraAgent().run(lat=37.8, lon=-122.4)

    _assert_camera_contract(r)
    assert r.detected is True
    assert r.confidence == pytest.approx(0.73)
    assert r.image_url == "https://example.com/still.jpg"
    assert r.raw == alert_payload
    assert r.telemetry["http_max_attempts"] >= 1


@pytest.mark.asyncio
async def test_camera_schema_event_image_only():
    with (
        patch(
            "app.services.ai.agents.camera.httpx_get_json",
            new_callable=AsyncMock,
        ) as gj,
        patch.object(CameraAgent, "_run_yolo", new_callable=AsyncMock, return_value=(0.1, False)),
        patch("app.services.ai.agents.camera.settings.alertca_api_key", ""),
    ):
        r = await CameraAgent().run(lat=37.0, lon=-122.0, image_url="https://x/y.jpg")

    gj.assert_not_called()
    _assert_camera_contract(r)
    assert r.confidence == pytest.approx(0.1)
    assert r.detected is False
    assert r.image_url == "https://x/y.jpg"
    assert r.raw.get("source") == "event_image_url"


@pytest.mark.asyncio
async def test_camera_schema_missing_key_degraded():
    with patch("app.services.ai.agents.camera.settings.alertca_api_key", ""):
        r = await CameraAgent().run(lat=37.0, lon=-122.0, image_url=None)

    _assert_camera_contract(r)
    assert r.confidence == 0.0
    assert r.detected is False
    assert r.image_url is None
    assert r.raw.get("error") == "missing ALERTCA_API_KEY"


# --- Satellite --------------------------------------------------------------


@pytest.mark.asyncio
async def test_satellite_schema_with_hotspots():
    firms = {"data": [{"frp": 45.0, "latitude": "37", "longitude": "-122"}]}
    with (
        patch(
            "app.services.ai.agents.satellite.httpx_get_json",
            new_callable=AsyncMock,
            return_value=firms,
        ),
        patch("app.services.ai.agents.satellite.settings.nasa_firms_map_key", "key"),
        patch("app.services.ai.agents.satellite.settings.collection_cache_ttl_sec", 0),
    ):
        r = await SatelliteAgent().run(lat=37.5, lon=-122.5)

    _assert_satellite_contract(r)
    assert r.hotspot_detected is True
    assert r.thermal_confidence == pytest.approx(min(45.0 / 100.0, 1.0))
    assert isinstance(r.raw["hotspots"], list)
    assert len(r.raw["hotspots"]) == 1
    assert r.telemetry.get("cache_hit") is False


@pytest.mark.asyncio
async def test_satellite_schema_empty_and_missing_key():
    with (
        patch(
            "app.services.ai.agents.satellite.httpx_get_json",
            new_callable=AsyncMock,
            return_value={"data": []},
        ),
        patch("app.services.ai.agents.satellite.settings.nasa_firms_map_key", "k"),
    ):
        r_clear = await SatelliteAgent().run(lat=1.0, lon=1.0)
    _assert_satellite_contract(r_clear)
    assert r_clear.hotspot_detected is False
    assert r_clear.thermal_confidence == 0.0

    with patch("app.services.ai.agents.satellite.settings.nasa_firms_map_key", ""):
        r_skip = await SatelliteAgent().run(lat=1.0, lon=1.0)
    _assert_satellite_contract(r_skip)
    assert r_skip.raw.get("error") == "missing NASA_FIRMS_MAP_KEY"


# --- Weather ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_weather_schema_success():
    owm = {
        "cod": 200,
        "wind": {"speed": 5.5, "deg": 270.0},
        "main": {"humidity": 33.0},
    }
    with (
        patch(
            "app.services.ai.agents.weather.httpx_get_json",
            new_callable=AsyncMock,
            return_value=owm,
        ),
        patch("app.services.ai.agents.weather.settings.openweathermap_api_key", "owm"),
        patch("app.services.ai.agents.weather.settings.collection_cache_ttl_sec", 0),
    ):
        r = await WeatherAgent().run(lat=34.05, lon=-118.25)

    _assert_weather_contract(r)
    assert r.wind_speed == pytest.approx(5.5)
    assert r.wind_direction == pytest.approx(270.0)
    assert r.humidity == pytest.approx(33.0)
    assert 0.0 <= r.spread_risk <= 1.0
    assert r.raw == owm
    assert r.telemetry.get("cache_hit") is False


@pytest.mark.asyncio
async def test_weather_schema_missing_key_and_logical_error():
    with patch("app.services.ai.agents.weather.settings.openweathermap_api_key", ""):
        r = await WeatherAgent().run(lat=34.0, lon=-118.0)
    _assert_weather_contract(r)
    assert r.spread_risk == 0.0
    assert "OPENWEATHERMAP" in (r.raw.get("error") or "")

    bad = {"cod": "404", "message": "not found"}
    with (
        patch(
            "app.services.ai.agents.weather.httpx_get_json",
            new_callable=AsyncMock,
            return_value=bad,
        ),
        patch("app.services.ai.agents.weather.settings.openweathermap_api_key", "k"),
    ):
        r2 = await WeatherAgent().run(lat=91.0, lon=0.0)
    _assert_weather_contract(r2)
    assert r2.wind_speed == 0.0
    assert r2.spread_risk == 0.0
    assert "openweather_api" in (r2.raw.get("error") or "")
