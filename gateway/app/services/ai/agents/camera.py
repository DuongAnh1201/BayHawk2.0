"""Incident-area fire evidence via **NASA FIRMS** (default) or optional YOLO on a snapshot.

Without ``image_url``, queries the same NASA FIRMS **Area API** as the satellite stage,
using a bounding box around ``(lat, lon)`` (``FIRMS_CAMERA_BBOX_HALF_DEG``, else
``FIRMS_BBOX_HALF_DEG``). ``CameraResult.confidence`` is the normalized hotspot / FRP score.

With ``image_url``, runs YOLOv8 on that image (e.g. operator-provided still).

Helpers ``first_camera_image_url`` / ``_camera_list`` remain for parsing legacy JSON shapes
in tests and integrations.
"""
from __future__ import annotations

import asyncio
import logging
import pathlib
import tempfile
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import logfire
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ultralytics import YOLO

from app.config import settings
from app.db.models import Camera as CameraRow
from app.db.models import ScanResult
from app.services.ai.schemas.pipeline import CameraResult
from app.services.storage import upload_snapshot

from .base import BaseAgent
from .firms_area import (
    fetch_firms_area_json,
    firms_bbox_wsen,
    parse_hotspots,
    thermal_confidence_from_hotspots,
)
from .geo_hints import haversine_km, log_if_outside_california, stage_location_metadata
from .http_retry import httpx_get_bytes

logger = logging.getLogger(__name__)

_FIRE_CLASSES = {"fire", "smoke"}

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
    """Best-effort image URL from common partner JSON shapes."""
    for cam in _camera_list(payload):
        url = _image_url_from_camera_entry(cam)
        if url:
            return url
    return None


class CameraAgent(BaseAgent):
    name = "camera"

    def __init__(self) -> None:
        self._model: YOLO | None = None

    def _telemetry_base(
        self,
        lat: float,
        lon: float,
        *,
        bbox_wsen: str | None = None,
        focus_radius_km: float | None = None,
    ) -> dict[str, Any]:
        return {
            "http_max_attempts": settings.collection_http_max_attempts,
            "yolo_imgsz": settings.yolo_inference_imgsz,
            "location": stage_location_metadata(lat, lon, bbox_wsen=bbox_wsen, focus_radius_km=focus_radius_km),
        }

    def _model_instance(self) -> YOLO:
        if self._model is None:
            self._model = YOLO(settings.yolo_model_path)
        return self._model

    async def _run_yolo(self, url: str) -> tuple[float, bool]:
        """Download image from url, run YOLOv8, return (confidence, detected)."""
        img_bytes = await httpx_get_bytes(
            url,
            timeout=15.0,
            max_attempts=settings.collection_http_max_attempts,
            label="camera_image",
        )

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_bytes)
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

    async def capture_snapshot(
        self,
        image_url: str,
        *,
        camera_id: int | str = "unknown",
    ) -> tuple[pathlib.Path, str]:
        """Download one frozen frame, upload JPEG to Supabase Storage, return temp path + public URL.

        YOLO reads the temp file; the temp file must be deleted by the caller.
        If Supabase is not configured, ``snapshot_url`` is ``""`` but bytes are still captured.
        """
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        object_path = f"cam{camera_id}_{ts}.jpg"
        img_bytes = await httpx_get_bytes(
            image_url,
            timeout=15.0,
            max_attempts=settings.collection_http_max_attempts,
            label="snapshot_capture",
        )
        snapshot_url = await asyncio.to_thread(upload_snapshot, img_bytes, object_path)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = pathlib.Path(tmp.name)

        return tmp_path, snapshot_url

    async def detect_on_snapshot(
        self,
        image_url: str,
        *,
        camera_id: int | str = "unknown",
    ) -> tuple[float, bool, str]:
        """Capture one frozen frame, run YOLO on that copy, return ``(confidence, detected, snapshot_url)``."""
        if settings.is_mock:
            return 0.0, False, ""
        tmp_path, snapshot_url = await self.capture_snapshot(image_url, camera_id=camera_id)
        try:
            conf, det = await self._run_yolo_on_file(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
        return conf, det, snapshot_url

    async def _run_yolo_on_file(self, path: pathlib.Path) -> tuple[float, bool]:
        """Run YOLOv8 on an already-saved image file."""
        model = self._model_instance()
        results = model.predict(
            str(path),
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

    async def run_multi(
        self,
        *,
        lat: float,
        lon: float,
        session: AsyncSession,
        focus_radius_km: float | None = None,
        **_,
    ) -> CameraResult:
        """All active DB-registered cameras within ``focus_radius_km`` (default ``FOCUS_RADIUS_KM``)."""
        radius_km = (
            settings.focus_radius_km
            if focus_radius_km is None or focus_radius_km <= 0
            else float(focus_radius_km)
        )
        loc_meta = stage_location_metadata(lat, lon, focus_radius_km=radius_km)
        with logfire.span(
            "agent.camera.multi",
            lat=lat,
            lon=lon,
            radius_km=radius_km,
            is_mock=settings.is_mock,
        ):
            t0 = time.perf_counter()
            if settings.is_mock:
                result = CameraResult(
                    confidence=0.87,
                    detected=True,
                    image_url="https://mock.example.org/focus-multi.jpg",
                    raw={
                        "focus_multi": True,
                        "is_mock": True,
                        "per_camera": [],
                        "location": loc_meta,
                        "center": {"lat": lat, "lon": lon},
                    },
                    telemetry={**self._telemetry_base(lat, lon), "location": loc_meta},
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                )
                logfire.info("camera.multi mock: confidence={c}", c=result.confidence)
                return result

            log_if_outside_california(lat, lon, context="camera.multi")
            res = await session.execute(select(CameraRow).where(CameraRow.is_active.is_(True)))
            all_cams: list[CameraRow] = list(res.scalars().all())
            nearby = [c for c in all_cams if haversine_km(lat, lon, c.lat, c.lon) <= radius_km]

            if not nearby:
                return CameraResult(
                    confidence=0.0,
                    detected=False,
                    image_url=None,
                    raw={
                        "focus_multi": True,
                        "nearby_cameras": 0,
                        "per_camera": [],
                        "center": {"lat": lat, "lon": lon},
                        "location": loc_meta,
                    },
                    telemetry={**self._telemetry_base(lat, lon), "location": loc_meta},
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                )

            per_camera: list[dict[str, Any]] = []
            triples: list[tuple[CameraRow, float, bool, str]] = []

            async def _one(cam: CameraRow) -> tuple[CameraRow, float, bool, str]:
                conf, det, snap = await self.detect_on_snapshot(cam.image_url, camera_id=cam.id)
                return cam, conf, det, snap

            batch_size = max(1, settings.scan_camera_batch_size)
            for i in range(0, len(nearby), batch_size):
                chunk = nearby[i : i + batch_size]
                chunk_out = await asyncio.gather(*[_one(c) for c in chunk], return_exceptions=True)
                for item in chunk_out:
                    if isinstance(item, BaseException):
                        logger.exception("multi-camera YOLO failed for a camera", exc_info=item)
                        continue
                    cam, conf, det, snap = item
                    triples.append((cam, conf, det, snap))
                    per_camera.append(
                        {
                            "id": cam.id,
                            "name": cam.name,
                            "lat": cam.lat,
                            "lon": cam.lon,
                            "confidence": conf,
                            "detected": det,
                            "image_url": cam.image_url,
                            "snapshot_url": snap,
                        }
                    )
                    captured_at = (
                        datetime.now(timezone.utc)
                        .replace(microsecond=0)
                        .isoformat()
                        .replace("+00:00", "Z")
                    )
                    session.add(
                        ScanResult(
                            camera_id=cam.id,
                            confidence=conf,
                            detected=det,
                            scan_type="focus",
                            observed_lat=cam.lat,
                            observed_lon=cam.lon,
                            snapshot_url=snap or None,
                            scan_metadata={
                                "mode": "focus_multi_yolo",
                                "location": stage_location_metadata(
                                    cam.lat,
                                    cam.lon,
                                    focus_radius_km=radius_km,
                                ),
                                "focus_center": {"lat": lat, "lon": lon},
                                "camera": {"id": cam.id, "name": cam.name},
                                "image_url": cam.image_url,
                                "snapshot_url": snap,
                                "analysis": {
                                    "engine": "yolo",
                                    "model_path": settings.yolo_model_path,
                                    "imgsz": settings.yolo_inference_imgsz,
                                },
                                "captured_at": captured_at,
                            },
                        )
                    )

            confidences = [c for _, c, _, _ in triples]
            best_conf = max(confidences) if confidences else 0.0
            best_detected = any(d for _, _, d, _ in triples)
            fire_frames = [(cam, c) for cam, c, d, _ in triples if d]
            if fire_frames:
                cam_pick, _ = max(fire_frames, key=lambda x: x[1])
                best_image_url = cam_pick.image_url
            else:
                best_image_url = nearby[0].image_url

            await session.commit()

            logfire.info(
                "camera.multi: cameras={n} detected={d} best_conf={c}",
                n=len(nearby),
                d=best_detected,
                c=best_conf,
            )
            return CameraResult(
                confidence=best_conf,
                detected=best_detected,
                image_url=best_image_url,
                raw={
                    "focus_multi": True,
                    "nearby_cameras": len(nearby),
                    "per_camera": per_camera,
                    "center": {"lat": lat, "lon": lon},
                    "location": loc_meta,
                },
                telemetry={**self._telemetry_base(lat, lon), "location": loc_meta},
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
            )

    async def run(
        self,
        *,
        lat: float,
        lon: float,
        image_url: str | None = None,
        focus_radius_km: float | None = None,
        **_,
    ) -> CameraResult:
        fr_km = focus_radius_km if focus_radius_km is not None and focus_radius_km > 0 else None
        with logfire.span("agent.camera", lat=lat, lon=lon, is_mock=settings.is_mock):
            t0 = time.perf_counter()
            if settings.is_mock:
                result = CameraResult(
                    confidence=0.87,
                    detected=True,
                    image_url=image_url or None,
                    raw={
                        "source": "mock",
                        "hotspots": [{"frp": 87.0, "latitude": lat, "longitude": lon}],
                        "location": stage_location_metadata(lat, lon, focus_radius_km=fr_km),
                    },
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                )
                logfire.info("camera mock: confidence={c}", c=result.confidence)
                return result

            log_if_outside_california(lat, lon, context="camera")
            bbox_half = settings.firms_camera_bbox_half_deg
            frp_norm = settings.firms_frp_normalize
            max_attempts = settings.collection_http_max_attempts
            telemetry: dict[str, Any] = {
                **self._telemetry_base(lat, lon, focus_radius_km=fr_km),
                "bbox_half_deg": bbox_half,
                "firms_source": settings.nasa_firms_source,
                "firms_area_day_range": settings.firms_area_day_range,
                "frp_normalize": frp_norm,
            }

            if image_url:
                img_loc = stage_location_metadata(lat, lon, focus_radius_km=fr_km)
                raw: dict[str, Any] = {
                    "source": "event_image_url",
                    "location": img_loc,
                    "note": "Image pixels are not geocoded; incident_lat/lon are the alert anchor for focus radius.",
                }
                url: str | None = image_url
                confidence, detected = await self._run_yolo(url)
                logfire.info("camera: yolo detected={d} confidence={c}", d=detected, c=confidence)
                return CameraResult(
                    confidence=confidence,
                    detected=detected,
                    image_url=url,
                    raw=raw,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry=telemetry,
                )

            if not (settings.nasa_firms_map_key or "").strip():
                return CameraResult(
                    confidence=0.0,
                    detected=False,
                    image_url=None,
                    raw={
                        "error": "missing NASA_FIRMS_MAP_KEY",
                        "location": stage_location_metadata(lat, lon, focus_radius_km=fr_km),
                    },
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry=telemetry,
                )

            bbox = firms_bbox_wsen(lat, lon, bbox_half)
            telemetry["location"] = stage_location_metadata(lat, lon, bbox_wsen=bbox, focus_radius_km=fr_km)
            try:
                data = await fetch_firms_area_json(
                    bbox,
                    timeout=12.0,
                    max_attempts=max_attempts,
                    label="nasa_firms_camera",
                )
            except (httpx.RequestError, httpx.HTTPError) as exc:
                logfire.warning("camera: FIRMS fetch failed: {e}", e=str(exc))
                return CameraResult(
                    confidence=0.0,
                    detected=False,
                    image_url=None,
                    raw={"error": str(exc), "location": stage_location_metadata(lat, lon, bbox_wsen=bbox, focus_radius_km=fr_km)},
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    telemetry=telemetry,
                )

            hotspots = parse_hotspots(data)
            confidence, detected = thermal_confidence_from_hotspots(hotspots, frp_norm)
            raw = {
                "source": "nasa_firms",
                "bbox": bbox,
                "hotspots": hotspots,
                "location": stage_location_metadata(lat, lon, bbox_wsen=bbox, focus_radius_km=fr_km),
            }

            logfire.info("camera: FIRMS detected={d} confidence={c}", d=detected, c=confidence)
            return CameraResult(
                confidence=confidence,
                detected=detected,
                image_url=None,
                raw=raw,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                telemetry=telemetry,
            )
