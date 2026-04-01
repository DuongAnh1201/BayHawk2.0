"""California wildfire camera evidence via **ALERTCalifornia** (UC San Diego).

Primary data source (state camera network, ~1,200 HD cameras):
  • Program: https://alertcalifornia.org/
  • Live map: https://cameras.alertcalifornia.org/

API access (partner / authorized token required; not fully public):
  • This agent calls the nearby-cameras endpoint on ``alertcalifornia.org`` using
    ``ALERTCA_API_KEY`` (Bearer). Obtain credentials through ALERTCalifornia /
    program partners.

Inference:
  • YOLOv8 on the nearest camera still image or an ``image_url`` supplied by the
    pipeline event (fire/smoke class scores → confidence).
"""
from __future__ import annotations

import logging
import pathlib
import tempfile
import time
from typing import Any

from ultralytics import YOLO

from app.config import settings
from app.services.ai.schemas.pipeline import CameraResult

from .base import BaseAgent
from .http_retry import httpx_get_bytes, httpx_get_json

logger = logging.getLogger(__name__)

_FIRE_CLASSES = {"fire", "smoke"}

# AlertCalifornia public API host (see https://alertcalifornia.org/)
_ALERTCA_NEARBY_URL = "https://www.alertcalifornia.org/api/cameras/nearby"

_IMAGE_KEYS = ("image_url", "imageUrl", "url", "latest_image_url", "still_url", "snapshot_url")


def _camera_list(payload: dict[str, Any]) -> list[Any]:
    cams = payload.get("cameras")
    if cams is None:
        cams = payload.get("data") or payload.get("results") or payload.get("items")
    if cams is None:
        return []
    return cams if isinstance(cams, list) else []


def _image_url_from_entry(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    for key in _IMAGE_KEYS:
        val = entry.get(key)
        if isinstance(val, str) and val.startswith(("http://", "https://")):
            return val
    return None


def _image_url_from_camera_entry(cam: Any) -> str | None:
    url = _image_url_from_entry(cam)
    if url:
        return url
    if isinstance(cam, dict):
        nested = cam.get("image") or cam.get("still")
        if isinstance(nested, dict):
            return _image_url_from_entry(nested)
    return None


def first_camera_image_url(payload: dict[str, Any]) -> str | None:
    """Best-effort image URL from common AlertCA / partner JSON shapes."""
    for cam in _camera_list(payload):
        url = _image_url_from_camera_entry(cam)
        if url:
            return url
    return None


class CameraAgent(BaseAgent):
    name = "camera"

    def __init__(self) -> None:
        self._model: YOLO | None = None

    def _model_instance(self) -> YOLO:
        if self._model is None:
            self._model = YOLO(settings.yolo_model_path)
        return self._model

    async def _fetch_alertca(self, lat: float, lon: float) -> dict[str, Any]:
        return await httpx_get_json(
            _ALERTCA_NEARBY_URL,
            params={"lat": lat, "lon": lon, "radius": 10},
            headers={"Authorization": f"Bearer {settings.alertca_api_key}"},
            timeout=12.0,
            max_attempts=settings.collection_http_max_attempts,
            label="alertca",
        )

    async def _run_yolo(self, url: str) -> tuple[float, bool]:
        """Download image from url, run YOLOv8, return (confidence, detected)."""
        content = await httpx_get_bytes(
            url,
            timeout=20.0,
            max_attempts=settings.collection_http_max_attempts,
            label="camera_image",
        )

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            model = self._model_instance()
            results = model.predict(
                tmp_path,
                imgsz=settings.yolo_inference_imgsz,
                verbose=False,
            )

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
        finally:
            pathlib.Path(tmp_path).unlink(missing_ok=True)

    async def run(self, *, lat: float, lon: float, image_url: str | None = None, **_) -> CameraResult:
        t0 = time.perf_counter()
        if settings.is_mock:
            return CameraResult(
                confidence=0.87,
                detected=True,
                image_url=image_url or "https://mock.alertcalifornia.org/cam001.jpg",
                raw={"cameras": [{"id": "mock-cam-001", "name": "Mock Ridge Cam"}]},
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                telemetry={
                    "http_max_attempts": settings.collection_http_max_attempts,
                    "yolo_imgsz": settings.yolo_inference_imgsz,
                },
            )
        raw = await self._fetch_alertca(lat, lon)
        url = image_url or first_camera_image_url(raw)

        confidence, detected = 0.0, False
        if url:
            try:
                confidence, detected = await self._run_yolo(url)
            except Exception as exc:
                logger.warning("YOLO / image download failed: %s", exc)
                raw = {**raw, "yolo_error": str(exc)}

        return CameraResult(
            confidence=confidence,
            detected=detected,
            image_url=url,
            raw=raw,
            latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            telemetry={
                "http_max_attempts": settings.collection_http_max_attempts,
                "yolo_imgsz": settings.yolo_inference_imgsz,
            },
        )
