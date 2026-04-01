"""Local fire-weather context via **OpenWeatherMap** Current Weather API.

Documentation:
  https://openweathermap.org/current

Coordinates are passed through from the incident (``lat``, ``lon``). For California
operations, use WGS84 decimal degrees inside the state; the same API serves any
location worldwide.
"""
from __future__ import annotations

from typing import Any

import httpx

from app.config import settings
from app.services.ai.schemas.pipeline import WeatherResult

from .base import BaseAgent


class WeatherAgent(BaseAgent):
    name = "weather"

    @staticmethod
    def _spread_risk(wind_speed: float, humidity: float) -> float:
        """Heuristic: high wind + low humidity → high spread risk (0–1)."""
        wind_factor = min(wind_speed / 20.0, 1.0)  # 20 m/s → 1.0
        humidity_factor = max(1.0 - humidity / 100.0, 0.0)
        return round(wind_factor * 0.6 + humidity_factor * 0.4, 3)

    async def run(self, *, lat: float, lon: float, **_) -> WeatherResult:
        if settings.is_mock:
            return WeatherResult(
                wind_speed=13.5,
                wind_direction=225.0,
                humidity=18.0,
                spread_risk=self._spread_risk(13.5, 18.0),
                raw={"wind": {"speed": 13.5, "deg": 225}, "main": {"humidity": 18}},
            )
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "lat": lat,
                    "lon": lon,
                    "appid": settings.openweathermap_api_key,
                    "units": "metric",
                },
            )
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

        wind = data.get("wind", {}) or {}
        main = data.get("main", {}) or {}
        wind_speed = float(wind.get("speed", 0))
        wind_direction = float(wind.get("deg", 0))
        humidity = float(main.get("humidity", 50))

        return WeatherResult(
            wind_speed=wind_speed,
            wind_direction=wind_direction,
            humidity=humidity,
            spread_risk=self._spread_risk(wind_speed, humidity),
            raw=data,
        )
