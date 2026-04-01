"""Background sweeps: periodic YOLO on every registered camera + optional FIRMS poll.

**Routine (default every ``SCAN_INTERVAL_SEC``, e.g. 300s):** for each active camera,
download one snapshot from ``image_url``, upload JPEG to **Supabase Storage** (when
configured), run **YOLO** on that frozen frame, and insert a ``ScanResult`` with
``snapshot_url``, ``observed_lat`` / ``observed_lon``, and ``scan_metadata``. Set
``SCANNER_ROUTINE_TRIGGERS_FOCUS=false`` to only log YOLO results without auto-running
the full pipeline on detections.

**Focus mode:** multi-camera YOLO within ``FOCUS_RADIUS_KM`` + full orchestrator pipeline
when routine YOLO detects fire (if ``SCANNER_ROUTINE_TRIGGERS_FOCUS``), when
``POST /ai/sweep-cameras?trigger_focus=true``, or when FIRMS finds a new hotspot in the
scanner bbox.

Use :func:`sweep_all_registered_cameras_to_db` for on-demand registry sweeps.
Satellite sweeps persist FIRMS hotspots to ``satellite_observations``.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import logfire
from sqlalchemy import select

from app.config import settings
from app.db.models import Camera as CameraRow
from app.db.models import SatelliteObservation
from app.db.models import ScanResult
from app.db.session import async_session_scope
from app.services.ai.agents.camera import CameraAgent
from app.services.ai.agents.firms_area import fetch_firms_area_json, parse_hotspots
from app.services.ai.agents.geo_hints import stage_location_metadata
from app.services.ai.agents.orchestrator import OrchestratorAgent
from app.services.ai.agents.satellite import _frp_value
from app.services.ai.schemas.pipeline import AlertEvent

logger = logging.getLogger(__name__)


def _parse_hotspot_coords(h: dict[str, Any]) -> tuple[float, float] | None:
    lat = h.get("latitude") or h.get("lat")
    lon = h.get("longitude") or h.get("lon")
    if lat is None or lon is None:
        return None
    try:
        return float(lat), float(lon)
    except (TypeError, ValueError):
        return None


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _routine_yolo_scan_metadata(
    cam: CameraRow,
    *,
    snapshot_url: str = "",
) -> dict[str, Any]:
    """Persisted with each scheduled / API routine row: location + how the snapshot was analyzed."""
    return {
        "mode": "routine_yolo_snapshot",
        "location": stage_location_metadata(cam.lat, cam.lon),
        "camera": {"id": cam.id, "name": cam.name},
        "image_url": cam.image_url,
        "snapshot_url": snapshot_url,
        "analysis": {
            "engine": "yolo",
            "model_path": settings.yolo_model_path,
            "imgsz": settings.yolo_inference_imgsz,
        },
        "sweep_interval_sec": settings.scan_interval_sec,
        "captured_at": _utc_timestamp(),
    }


@dataclass(frozen=True)
class RegistrySweepSummary:
    cameras_scanned: int
    scan_rows_inserted: int
    detection_triggers: int
    errors: int
    trigger_focus_on_detection: bool


@dataclass(frozen=True)
class SatelliteSweepSummary:
    observations_inserted: int
    focus_cells_considered: int
    focus_pipelines_run: int
    skipped_reason: str | None = None
    error_detail: str | None = None


async def sweep_all_registered_cameras_to_db(
    *,
    trigger_focus_on_detection: bool = False,
) -> RegistrySweepSummary:
    """Scan every **active** camera in the registry, persist ``ScanResult`` (+ lat/lon), optionally run focus pipeline."""
    if settings.database_url_async is None:
        raise RuntimeError("DATABASE_URL is not configured")
    return await ScannerService().persist_registry_camera_scan(
        trigger_focus_on_detection=trigger_focus_on_detection,
    )


async def run_satellite_sweep_now() -> SatelliteSweepSummary:
    """On-demand FIRMS wide-area sweep + DB rows + focus (same logic as scheduled job)."""
    if settings.database_url_async is None:
        raise RuntimeError("DATABASE_URL is not configured")
    return await ScannerService().persist_satellite_sweep()


class ScannerService:
    def __init__(self) -> None:
        self.camera_agent = CameraAgent()
        self.orchestrator = OrchestratorAgent()
        self._last_focus_at: dict[tuple[str, str], float] = {}

    def _focus_allowed(self, lat: float, lon: float) -> bool:
        key = (f"{lat:.2f}", f"{lon:.2f}")
        now = time.time()
        last = self._last_focus_at.get(key, 0.0)
        if now - last < settings.focus_cooldown_sec:
            logfire.info("scanner: focus cooldown skip cell={key}", key=key)
            return False
        self._last_focus_at[key] = now
        return True

    async def _run_focus_pipeline(
        self,
        lat: float,
        lon: float,
        *,
        trigger: str,
        focus_radius_km: float | None = None,
    ) -> bool:
        """Run focus pipeline if cooldown allows. Returns True if orchestrator completed."""
        if not self._focus_allowed(lat, lon):
            return False
        fr_km = (
            settings.focus_radius_km
            if focus_radius_km is None or focus_radius_km <= 0
            else float(focus_radius_km)
        )
        with logfire.span("scanner.focus", lat=lat, lon=lon, trigger=trigger, focus_radius_km=fr_km):
            try:
                async with async_session_scope() as session:
                    camera_res = await self.camera_agent.run_multi(
                        lat=lat,
                        lon=lon,
                        session=session,
                        focus_radius_km=fr_km,
                    )
                event = AlertEvent(
                    event_id=f"focus-{uuid.uuid4()}",
                    lat=lat,
                    lon=lon,
                    camera_id=None,
                    image_url=camera_res.image_url,
                    timestamp=_utc_timestamp(),
                    focus_radius_km=fr_km,
                )
                await self.orchestrator.run(event=event, camera_override=camera_res)
            except Exception:
                logger.exception("focus pipeline failed lat=%s lon=%s", lat, lon)
                return False
            return True

    async def persist_registry_camera_scan(
        self,
        *,
        trigger_focus_on_detection: bool,
    ) -> RegistrySweepSummary:
        """YOLO every active registered camera; write ``ScanResult`` with ``observed_lat``/``observed_lon``."""
        errors = 0
        scan_rows = 0
        detections = 0
        cameras_count = 0

        with logfire.span(
            "scanner.registry_camera_scan",
            is_mock=settings.is_mock,
            trigger_focus=trigger_focus_on_detection,
        ):
            if settings.is_mock:
                async with async_session_scope() as session:
                    res = await session.execute(select(CameraRow).where(CameraRow.is_active.is_(True)))
                    cams = list(res.scalars().all())
                    cameras_count = len(cams)
                    for cam in cams:
                        session.add(
                            ScanResult(
                                camera_id=cam.id,
                                confidence=0.0,
                                detected=False,
                                scan_type="routine",
                                observed_lat=cam.lat,
                                observed_lon=cam.lon,
                                scan_metadata=_routine_yolo_scan_metadata(cam),
                            )
                        )
                        scan_rows += 1
                    await session.commit()
                logfire.info(
                    "scanner: registry sweep mock stored {n} rows",
                    n=scan_rows,
                )
                return RegistrySweepSummary(
                    cameras_scanned=cameras_count,
                    scan_rows_inserted=scan_rows,
                    detection_triggers=0,
                    errors=0,
                    trigger_focus_on_detection=trigger_focus_on_detection,
                )

            async with async_session_scope() as session:
                res = await session.execute(select(CameraRow).where(CameraRow.is_active.is_(True)))
                cameras = list(res.scalars().all())

            cameras_count = len(cameras)
            if not cameras:
                logfire.info("scanner: no active cameras registered")
                return RegistrySweepSummary(
                    cameras_scanned=0,
                    scan_rows_inserted=0,
                    detection_triggers=0,
                    errors=0,
                    trigger_focus_on_detection=trigger_focus_on_detection,
                )

            batch_size = max(1, settings.scan_camera_batch_size)
            for i in range(0, len(cameras), batch_size):
                batch = cameras[i : i + batch_size]

                async def scan_one(cam: CameraRow) -> tuple[CameraRow, float, bool, str]:
                    conf, det, snap = await self.camera_agent.detect_on_snapshot(
                        cam.image_url,
                        camera_id=cam.id,
                    )
                    return cam, conf, det, snap

                out = await asyncio.gather(*[scan_one(c) for c in batch], return_exceptions=True)
                triggers: list[tuple[float, float]] = []
                async with async_session_scope() as session:
                    for item in out:
                        if isinstance(item, BaseException):
                            errors += 1
                            logger.exception("routine camera scan failed", exc_info=item)
                            continue
                        cam, conf, det, snap = item
                        session.add(
                            ScanResult(
                                camera_id=cam.id,
                                confidence=conf,
                                detected=det,
                                scan_type="routine",
                                observed_lat=cam.lat,
                                observed_lon=cam.lon,
                                snapshot_url=snap or None,
                                scan_metadata=_routine_yolo_scan_metadata(cam, snapshot_url=snap),
                            )
                        )
                        scan_rows += 1
                        if det:
                            detections += 1
                            triggers.append((cam.lat, cam.lon))
                    await session.commit()
                if trigger_focus_on_detection:
                    for flat, flon in triggers:
                        await self._run_focus_pipeline(flat, flon, trigger="camera")

        return RegistrySweepSummary(
            cameras_scanned=cameras_count,
            scan_rows_inserted=scan_rows,
            detection_triggers=detections,
            errors=errors,
            trigger_focus_on_detection=trigger_focus_on_detection,
        )

    async def camera_sweep(self) -> None:
        if not settings.scanner_enabled:
            return
        if settings.database_url_async is None:
            return
        with logfire.span("scanner.camera_sweep", is_mock=settings.is_mock):
            await self.persist_registry_camera_scan(
                trigger_focus_on_detection=settings.routine_triggers_focus,
            )

    async def persist_satellite_sweep(self) -> SatelliteSweepSummary:
        """Poll FIRMS over ``SCANNER_SATELLITE_BBOX``, insert ``satellite_observations``, run focus per cell."""
        with logfire.span("scanner.satellite_sweep", is_mock=settings.is_mock):
            if settings.is_mock:
                logfire.info("scanner: satellite sweep mock – skip FIRMS")
                return SatelliteSweepSummary(
                    0,
                    0,
                    0,
                    skipped_reason="is_mock",
                )
            key = (settings.nasa_firms_map_key or "").strip()
            if not key:
                logger.warning("scanner: NASA_FIRMS_MAP_KEY missing; satellite sweep skipped")
                return SatelliteSweepSummary(
                    0,
                    0,
                    0,
                    skipped_reason="missing_nasa_firms_map_key",
                )
            parts = [p.strip() for p in settings.scanner_satellite_bbox.split(",")]
            if len(parts) != 4:
                logger.warning("scanner: invalid SCANNER_SATELLITE_BBOX")
                return SatelliteSweepSummary(
                    0,
                    0,
                    0,
                    skipped_reason="invalid_scanner_satellite_bbox",
                )
            west, south, east, north = (float(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]))
            bbox = f"{west},{south},{east},{north}"
            try:
                data = await fetch_firms_area_json(
                    bbox,
                    timeout=25.0,
                    max_attempts=settings.collection_http_max_attempts,
                    label="scanner_firms",
                )
            except Exception as exc:
                logger.warning("scanner: FIRMS error %s", exc)
                return SatelliteSweepSummary(
                    0,
                    0,
                    0,
                    error_detail=str(exc),
                )
            hotspots = parse_hotspots(data)

            inserted = 0
            async with async_session_scope() as session:
                for h in hotspots:
                    if not isinstance(h, dict):
                        continue
                    coords = _parse_hotspot_coords(h)
                    if coords is None:
                        continue
                    lat, lon = coords
                    frp_v = _frp_value(h)
                    obs_raw = dict(h)
                    obs_raw["firms_source"] = settings.nasa_firms_source
                    obs_raw["firms_area_day_range"] = settings.firms_area_day_range
                    obs_raw["location_metadata"] = stage_location_metadata(
                        lat,
                        lon,
                        focus_radius_km=settings.focus_radius_km,
                    )
                    session.add(
                        SatelliteObservation(
                            lat=lat,
                            lon=lon,
                            frp=frp_v,
                            raw=obs_raw,
                        )
                    )
                    inserted += 1
                await session.commit()

            seen_latlon: set[tuple[str, str]] = set()
            focus_runs = 0
            for h in hotspots:
                if not isinstance(h, dict):
                    continue
                coords = _parse_hotspot_coords(h)
                if coords is None:
                    continue
                lat, lon = coords
                cell = (f"{lat:.2f}", f"{lon:.2f}")
                if cell in seen_latlon:
                    continue
                seen_latlon.add(cell)
                if await self._run_focus_pipeline(lat, lon, trigger="satellite"):
                    focus_runs += 1

            return SatelliteSweepSummary(
                observations_inserted=inserted,
                focus_cells_considered=len(seen_latlon),
                focus_pipelines_run=focus_runs,
            )

    async def satellite_sweep(self) -> None:
        if not settings.scanner_enabled:
            return
        if settings.database_url_async is None:
            return
        await self.persist_satellite_sweep()
