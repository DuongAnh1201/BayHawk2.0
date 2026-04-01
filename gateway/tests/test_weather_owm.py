"""OpenWeatherMap response edge cases."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.ai.agents.weather import WeatherAgent


@pytest.mark.asyncio
async def test_openweather_logical_error_cod_string():
    bad_payload = {"cod": "404", "message": "city not found"}

    with (
        patch(
            "app.services.ai.agents.weather.httpx_get_json",
            new_callable=AsyncMock,
            return_value=bad_payload,
        ),
        patch("app.services.ai.agents.weather.settings.openweathermap_api_key", "k"),
    ):
        r = await WeatherAgent().run(lat=91.0, lon=0.0)

    assert r.spread_risk == 0.0
    assert "openweather_api" in (r.raw or {}).get("error", "")


@pytest.mark.asyncio
async def test_openweather_accepts_cod_int_200():
    ok = {"cod": 200, "wind": {"speed": 1, "deg": 0}, "main": {"humidity": 50}}

    with (
        patch(
            "app.services.ai.agents.weather.httpx_get_json",
            new_callable=AsyncMock,
            return_value=ok,
        ),
        patch("app.services.ai.agents.weather.settings.openweathermap_api_key", "k"),
    ):
        r = await WeatherAgent().run(lat=36.0, lon=-119.0)

    assert r.wind_speed == 1.0
    assert r.raw == ok
