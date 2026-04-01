import httpx

from app.config import settings
from app.services.ai.schemas.pipeline import SatelliteResult

from .base import BaseAgent

_FRP_NORMALIZE = 100.0  # FRP value that maps to confidence 1.0


class SatelliteAgent(BaseAgent):
    name = "satellite"

    async def run(self, *, lat: float, lon: float, **_) -> SatelliteResult:
        # NASA FIRMS – active fire / hotspot data (VIIRS SNPP Near-Real-Time)
        bbox = f"{lon - 0.1},{lat - 0.1},{lon + 0.1},{lat + 0.1}"
        url = (
            f"https://firms.modaps.eosdis.nasa.gov/api/area/json/"
            f"{settings.nasa_firms_map_key}/VIIRS_SNPP_NRT/{bbox}/1"
        )

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        hotspots = data if isinstance(data, list) else data.get("data", [])
        hotspot_detected = len(hotspots) > 0
        thermal_confidence = 0.0

        if hotspot_detected:
            frp_values = [float(h["frp"]) for h in hotspots if h.get("frp")]
            if frp_values:
                thermal_confidence = min(max(frp_values) / _FRP_NORMALIZE, 1.0)

        return SatelliteResult(
            thermal_confidence=thermal_confidence,
            hotspot_detected=hotspot_detected,
            raw={"hotspots": hotspots},
        )
