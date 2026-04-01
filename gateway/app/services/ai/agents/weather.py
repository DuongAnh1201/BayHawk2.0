import httpx

from app.config import settings
from app.services.ai.schemas.pipeline import WeatherResult

from .base import BaseAgent


class WeatherAgent(BaseAgent):
    name = "weather"

    @staticmethod
    def _spread_risk(wind_speed: float, humidity: float) -> float:
        """Heuristic: high wind + low humidity → high spread risk (0–1)."""
        wind_factor = min(wind_speed / 20.0, 1.0)          # 20 m/s → 1.0
        humidity_factor = max(1.0 - humidity / 100.0, 0.0)
        return round(wind_factor * 0.6 + humidity_factor * 0.4, 3)

    async def run(self, *, lat: float, lon: float, **_) -> WeatherResult:
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
            data = resp.json()

        wind = data.get("wind", {})
        main = data.get("main", {})
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
