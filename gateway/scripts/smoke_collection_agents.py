"""Live smoke test for Camera, Satellite, and Weather agents.

Run from repo root (``uv run`` so ``gateway`` is on PYTHONPATH):

  uv run python gateway/scripts/smoke_collection_agents.py --lat 37.8 --lon -122.4

Env knobs (accuracy / speed / cost), see ``app/config.py``:
  COLLECTION_HTTP_MAX_ATTEMPTS — fewer = faster, less retry cost
  COLLECTION_CACHE_TTL_SEC — >0 reuses OWM + FIRMS for same area (saves quota + ms)
  YOLO_INFERENCE_IMGSZ — lower (e.g. 416) = faster inference, slightly less accuracy
  FIRMS_BBOX_HALF_DEG / FIRMS_FRP_NORMALIZE — satellite context + score calibration
  FUSION_THRESHOLD / FUSION_CAMERA_WEIGHT — fewer false positives vs recall

JSON output includes ``latency_ms`` and ``telemetry`` on each result.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_GATEWAY = Path(__file__).resolve().parents[1]
if str(_GATEWAY) not in sys.path:
    sys.path.insert(0, str(_GATEWAY))


async def _main() -> None:
    from dotenv import load_dotenv

    load_dotenv(_REPO / ".env")

    from app.services.ai.agents.camera import CameraAgent
    from app.services.ai.agents.satellite import SatelliteAgent
    from app.services.ai.agents.weather import WeatherAgent

    p = argparse.ArgumentParser(description="Run collection agents against live APIs.")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--image-url", type=str, default=None, help="Optional; skips AlertCA fetch when set.")
    args = p.parse_args()

    cam, sat, wx = CameraAgent(), SatelliteAgent(), WeatherAgent()
    c_res, s_res, w_res = await asyncio.gather(
        cam.run(lat=args.lat, lon=args.lon, image_url=args.image_url),
        sat.run(lat=args.lat, lon=args.lon),
        wx.run(lat=args.lat, lon=args.lon),
    )

    out = {
        "camera": c_res.model_dump(),
        "satellite": s_res.model_dump(),
        "weather": w_res.model_dump(),
    }
    print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(_main())
