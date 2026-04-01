"""TTL cache reduces duplicate OpenWeather / FIRMS calls."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.config import settings
from app.services.ai.agents.satellite import SatelliteAgent
from app.services.ai.agents.weather import WeatherAgent


@pytest.mark.asyncio
async def test_weather_cache_second_hit(monkeypatch):
    monkeypatch.setattr(settings, "collection_cache_ttl_sec", 300)
    monkeypatch.setattr(settings, "openweathermap_api_key", "k")
    payload = {
        "cod": 200,
        "wind": {"speed": 2.0, "deg": 180.0},
        "main": {"humidity": 55.0},
    }
    with patch(
        "app.services.ai.agents.weather.httpx_get_json",
        new_callable=AsyncMock,
        return_value=payload,
    ) as get_json:
        agent = WeatherAgent()
        r1 = await agent.run(lat=36.7783, lon=-119.4179)
        r2 = await agent.run(lat=36.7783, lon=-119.4179)
    assert get_json.await_count == 1
    assert r1.telemetry.get("cache_hit") is False
    assert r2.telemetry.get("cache_hit") is True


@pytest.mark.asyncio
async def test_satellite_cache_second_hit(monkeypatch):
    monkeypatch.setattr(settings, "collection_cache_ttl_sec", 300)
    monkeypatch.setattr(settings, "nasa_firms_map_key", "mapkey")
    firms = {"data": [{"frp": 10.0}]}
    with patch(
        "app.services.ai.agents.satellite.httpx_get_json",
        new_callable=AsyncMock,
        return_value=firms,
    ) as get_json:
        agent = SatelliteAgent()
        r1 = await agent.run(lat=37.0, lon=-122.0)
        r2 = await agent.run(lat=37.0, lon=-122.0)
    assert get_json.await_count == 1
    assert r1.telemetry.get("cache_hit") is False
    assert r2.telemetry.get("cache_hit") is True
