"""Unit tests for Camera, Satellite, and Weather collection agents (HTTP mocked)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.services.ai.agents.camera import CameraAgent
from app.services.ai.agents.satellite import SatelliteAgent
from app.services.ai.agents.weather import WeatherAgent


@pytest.mark.asyncio
async def test_camera_agent_alertca_and_yolo():
    alert_payload = {"cameras": [{"image_url": "https://example.com/cam.jpg", "id": "1"}]}

    with (
        patch(
            "app.services.ai.agents.camera.httpx_get_json",
            new_callable=AsyncMock,
            return_value=alert_payload,
        ),
        patch.object(CameraAgent, "_run_yolo", new_callable=AsyncMock, return_value=(0.82, True)),
        patch("app.services.ai.agents.camera.settings.alertca_api_key", "test-token"),
    ):
        agent = CameraAgent()
        result = await agent.run(lat=37.8, lon=-122.4)

    assert result.detected is True
    assert result.confidence == pytest.approx(0.82)
    assert result.image_url == "https://example.com/cam.jpg"
    assert result.raw == alert_payload
    assert result.latency_ms is not None


@pytest.mark.asyncio
async def test_camera_agent_uses_explicit_image_url_skips_alertca():
    """When ``image_url`` is set, do not call ALERTCalifornia (faster, works without key)."""

    with (
        patch("app.services.ai.agents.camera.httpx_get_json", new_callable=AsyncMock) as get_json,
        patch("app.services.ai.agents.camera.httpx_get_bytes", new_callable=AsyncMock) as get_bytes,
        patch.object(CameraAgent, "_run_yolo", new_callable=AsyncMock, return_value=(0.5, True)),
        patch("app.services.ai.agents.camera.settings.alertca_api_key", ""),
    ):
        agent = CameraAgent()
        result = await agent.run(lat=37.0, lon=-122.0, image_url="https://override.com/x.jpg")

    get_json.assert_not_called()
    get_bytes.assert_not_called()
    assert result.image_url == "https://override.com/x.jpg"
    assert result.confidence == pytest.approx(0.5)
    assert result.raw == {"source": "event_image_url"}


@pytest.mark.asyncio
async def test_camera_agent_no_image_zero_confidence():
    with (
        patch(
            "app.services.ai.agents.camera.httpx_get_json",
            new_callable=AsyncMock,
            return_value={"cameras": []},
        ),
        patch.object(CameraAgent, "_run_yolo", new_callable=AsyncMock) as yolo,
        patch("app.services.ai.agents.camera.settings.alertca_api_key", "test-token"),
    ):
        agent = CameraAgent()
        result = await agent.run(lat=37.0, lon=-122.0)

    yolo.assert_not_called()
    assert result.confidence == 0.0
    assert result.detected is False


@pytest.mark.asyncio
async def test_camera_agent_missing_key_no_image():
    with patch("app.services.ai.agents.camera.httpx_get_json", new_callable=AsyncMock) as get_json:
        result = await CameraAgent().run(lat=37.0, lon=-122.0, image_url=None)

    get_json.assert_not_called()
    assert result.confidence == 0.0
    assert result.raw and "missing ALERTCA_API_KEY" in result.raw.get("error", "")


@pytest.mark.asyncio
async def test_camera_agent_alertca_http_error():
    with (
        patch(
            "app.services.ai.agents.camera.httpx_get_json",
            new_callable=AsyncMock,
            side_effect=httpx.RequestError("upstream failure"),
        ),
        patch.object(CameraAgent, "_run_yolo", new_callable=AsyncMock) as yolo,
        patch("app.services.ai.agents.camera.settings.alertca_api_key", "x"),
    ):
        result = await CameraAgent().run(lat=37.0, lon=-122.0)

    yolo.assert_not_called()
    assert result.confidence == 0.0
    assert "error" in (result.raw or {})


@pytest.mark.asyncio
async def test_satellite_agent_hotspots_dict_payload():
    frp = 80.0
    firms_payload = {"data": [{"frp": str(frp), "latitude": "37", "longitude": "-122"}]}

    with (
        patch(
            "app.services.ai.agents.satellite.httpx_get_json",
            new_callable=AsyncMock,
            return_value=firms_payload,
        ),
        patch("app.services.ai.agents.satellite.settings.nasa_firms_map_key", "map-key"),
    ):
        agent = SatelliteAgent()
        result = await agent.run(lat=37.5, lon=-122.5)

    assert result.hotspot_detected is True
    assert result.thermal_confidence == pytest.approx(min(frp / 100.0, 1.0))
    assert result.raw["hotspots"] == firms_payload["data"]


@pytest.mark.asyncio
async def test_satellite_agent_missing_map_key():
    with patch("app.services.ai.agents.satellite.httpx_get_json", new_callable=AsyncMock) as get_json:
        result = await SatelliteAgent().run(lat=1.0, lon=1.0)

    get_json.assert_not_called()
    assert result.hotspot_detected is False
    assert "NASA_FIRMS_MAP_KEY" in (result.raw or {}).get("error", "")


@pytest.mark.asyncio
async def test_satellite_agent_hotspots_list_payload_capped():
    firms_payload = [{"frp": 250.0}]

    with (
        patch(
            "app.services.ai.agents.satellite.httpx_get_json",
            new_callable=AsyncMock,
            return_value=firms_payload,
        ),
        patch("app.services.ai.agents.satellite.settings.nasa_firms_map_key", "k"),
    ):
        result = await SatelliteAgent().run(lat=1.0, lon=1.0)

    assert result.hotspot_detected is True
    assert result.thermal_confidence == 1.0


@pytest.mark.asyncio
async def test_satellite_agent_no_hotspots():
    with (
        patch(
            "app.services.ai.agents.satellite.httpx_get_json",
            new_callable=AsyncMock,
            return_value={"data": []},
        ),
        patch("app.services.ai.agents.satellite.settings.nasa_firms_map_key", "k"),
    ):
        result = await SatelliteAgent().run(lat=1.0, lon=1.0)

    assert result.hotspot_detected is False
    assert result.thermal_confidence == 0.0


@pytest.mark.asyncio
async def test_weather_agent_openweather_fields_and_spread_risk():
    owm_payload = {
        "cod": 200,
        "wind": {"speed": 10.0, "deg": 90.0},
        "main": {"humidity": 40.0},
    }

    with (
        patch(
            "app.services.ai.agents.weather.httpx_get_json",
            new_callable=AsyncMock,
            return_value=owm_payload,
        ),
        patch("app.services.ai.agents.weather.settings.openweathermap_api_key", "owm"),
    ):
        result = await WeatherAgent().run(lat=34.0, lon=-118.0)

    assert result.wind_speed == pytest.approx(10.0)
    assert result.wind_direction == pytest.approx(90.0)
    assert result.humidity == pytest.approx(40.0)
    wind_factor = min(10.0 / 20.0, 1.0)
    humidity_factor = max(1.0 - 40.0 / 100.0, 0.0)
    expected_spread = round(wind_factor * 0.6 + humidity_factor * 0.4, 3)
    assert result.spread_risk == pytest.approx(expected_spread)


@pytest.mark.asyncio
async def test_weather_agent_missing_api_key():
    with patch("app.services.ai.agents.weather.httpx_get_json", new_callable=AsyncMock) as get_json:
        result = await WeatherAgent().run(lat=34.0, lon=-118.0)

    get_json.assert_not_called()
    assert result.spread_risk == 0.0
    assert "OPENWEATHERMAP_API_KEY" in (result.raw or {}).get("error", "")


def test_spread_risk_extremes():
    assert WeatherAgent._spread_risk(20.0, 0.0) == 1.0
    assert WeatherAgent._spread_risk(0.0, 100.0) == 0.0
