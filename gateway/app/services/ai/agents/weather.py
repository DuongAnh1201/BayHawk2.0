"""Local fire-weather context via **OpenWeatherMap** Current Weather API.

Documentation:
  https://openweathermap.org/current

Coordinates are passed through from the incident (``lat``, ``lon``). For California
operations, use WGS84 decimal degrees inside the state; the same API serves any
location worldwide.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx
import logfire

from app.config import settings
from app.services.ai.schemas.pipeline import WeatherResult

from .base import BaseAgent
from .collection_cache import get_named_cache
from .geo_hints import log_if_outside_california
from .http_retry import httpx_get_json

logger = logging.getLogger(__name__)

_OWM_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"


def _owm_ok(payload: dict[str, Any]) -> bool:
    cod = payload.get("cod")
    if cod is None:
        return True
    return cod == 200 or cod == "200"


def _weather_cache_key(lat: float, lon: float) -> str:
    return f"{round(lat, 4)},{round(lon, 4)}"


class WeatherAgent(BaseAgent):
    name = "weather"

    @staticmethod
    def _spread_risk(wind_speed: float, humidity: float) -> float:
        """Heuristic: high wind + low humidity → high spread risk (0–1)."""
        wind_factor = min(wind_speed / 20.0, 1.0)
        humidity_factor = max(1.0 - humidity / 100.0, 0.0)
        return round(wind_factor * 0.6 + humidity_factor * 0.4, 3)

    async def run(self, *, lat: float, lon: float, **_) -> WeatherResult:
        with logfire.span("agent.weather", lat=lat, lon=lon, is_mock=settings.is_mock):
            t0 = time.perf_counter()
            if settings.is_mock:
                result = WeatherResult(
                    wind_speed=13.5,
                    wind_direction=225.0,
                    humidity=18.0,
                    spread_risk=self._spread_risk(13.5, 18.0),
                    raw={"wind": {"speed": 13.5, "deg": 225}, "main": {"humidity": 18}},
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry={},
                )
                logfire.info("weather mock: spread_risk={sr}", sr=result.spread_risk)
                return result

            log_if_outside_california(lat, lon, context="weather")
            max_attempts = settings.collection_http_max_attempts

            if not (settings.openweathermap_api_key or "").strip():
                logger.warning("OPENWEATHERMAP_API_KEY missing; weather stage skipped")
                return WeatherResult(
                    wind_speed=0.0,
                    wind_direction=0.0,
                    humidity=0.0,
                    spread_risk=0.0,
                    raw={"error": "missing OPENWEATHERMAP_API_KEY"},
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry={"http_max_attempts": max_attempts},
                )

            cache = get_named_cache("openweather", settings.collection_cache_ttl_sec)
            wkey = _weather_cache_key(lat, lon)
            if cache is not None:
                cached = await cache.get(wkey)
                if cached is not None:
                    return cached.model_copy(
                        deep=True,
                        update={
                            "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                            "telemetry": {
                                **(cached.telemetry or {}),
                                "cache_hit": True,
                                "api_calls_saved": 1,
                            },
                        },
                    )

            try:
                data = await httpx_get_json(
                    _OWM_CURRENT_URL,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "appid": settings.openweathermap_api_key,
                        "units": "metric",
                    },
                    timeout=12.0,
                    max_attempts=max_attempts,
                    label="openweather",
                )
            except httpx.HTTPError as exc:
                logger.warning("OpenWeatherMap HTTP error: %s", exc)
                return WeatherResult(
                    wind_speed=0.0,
                    wind_direction=0.0,
                    humidity=0.0,
                    spread_risk=0.0,
                    raw={"error": str(exc)},
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry={"http_max_attempts": max_attempts},
                )
            except Exception as exc:
                logger.warning("OpenWeatherMap request failed: %s", exc)
                return WeatherResult(
                    wind_speed=0.0,
                    wind_direction=0.0,
                    humidity=0.0,
                    spread_risk=0.0,
                    raw={"error": str(exc)},
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry={"http_max_attempts": max_attempts},
                )

            if not isinstance(data, dict) or not _owm_ok(data):
                msg = data.get("message", "unknown error") if isinstance(data, dict) else "invalid response"
                logger.warning("OpenWeatherMap logical error: %s", msg)
                base = dict(data) if isinstance(data, dict) else {}
                base["error"] = f"openweather_api: {msg}"
                return WeatherResult(
                    wind_speed=0.0,
                    wind_direction=0.0,
                    humidity=0.0,
                    spread_risk=0.0,
                    raw=base,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry={"http_max_attempts": max_attempts},
                )

            wind = data.get("wind", {}) or {}
            main = data.get("main", {}) or {}
            wind_speed = float(wind.get("speed", 0))
            wind_direction = float(wind.get("deg", 0))
            humidity = float(main.get("humidity", 50))
            spread_risk = self._spread_risk(wind_speed, humidity)

            logfire.info("weather: wind={w} humidity={h} spread_risk={sr}", w=wind_speed, h=humidity, sr=spread_risk)
            result = WeatherResult(
                wind_speed=wind_speed,
                wind_direction=wind_direction,
                humidity=humidity,
                spread_risk=spread_risk,
                raw=data,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                telemetry={"http_max_attempts": max_attempts, "cache_hit": False},
            )

            if cache is not None:
                await cache.set(wkey, result)

            return result
