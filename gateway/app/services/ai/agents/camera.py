from __future__ import annotations

import pathlib
import tempfile

import httpx
from ultralytics import YOLO

from app.config import settings
from app.services.ai.schemas.pipeline import CameraResult

from .base import BaseAgent

_FIRE_CLASSES = {"fire", "smoke"}


class CameraAgent(BaseAgent):
    name = "camera"

    def __init__(self) -> None:
        self._model: YOLO | None = None

    # ── private helpers ────────────────────────────────────────────────────────

    def _model_instance(self) -> YOLO:
        if self._model is None:
            self._model = YOLO(settings.yolo_model_path)
        return self._model

    async def _fetch_alertca(self, lat: float, lon: float) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.alertcalifornia.org/api/cameras/nearby",
                params={"lat": lat, "lon": lon, "radius": 10},
                headers={"Authorization": f"Bearer {settings.alertca_api_key}"},
            )
            resp.raise_for_status()
            return resp.json()

    async def _run_yolo(self, url: str) -> tuple[float, bool]:
        """Download image from url, run YOLOv8, return (confidence, detected)."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            img_resp = await client.get(url)
            img_resp.raise_for_status()

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_resp.content)
            tmp_path = tmp.name

        model = self._model_instance()
        results = model(tmp_path)
        pathlib.Path(tmp_path).unlink(missing_ok=True)

        best_conf = 0.0
        detected = False
        for r in results:
            for box in r.boxes:
                cls_name = model.names[int(box.cls)]
                if cls_name in _FIRE_CLASSES:
                    conf = float(box.conf)
                    if conf > best_conf:
                        best_conf = conf
                        detected = True

        return best_conf, detected

    # ── public interface ───────────────────────────────────────────────────────

    async def run(self, *, lat: float, lon: float, image_url: str | None = None, **_) -> CameraResult:
        if settings.is_mock:
            return CameraResult(
                confidence=0.87,
                detected=True,
                image_url=image_url or "https://mock.alertcalifornia.org/cam001.jpg",
                raw={"cameras": [{"id": "mock-cam-001", "name": "Mock Ridge Cam"}]},
            )
        raw = await self._fetch_alertca(lat, lon)

        # Use caller-supplied URL or fall back to nearest AlertCA camera image
        url = image_url or (raw.get("cameras") or [{}])[0].get("image_url")

        confidence, detected = 0.0, False
        if url:
            confidence, detected = await self._run_yolo(url)

        return CameraResult(confidence=confidence, detected=detected, image_url=url, raw=raw)
