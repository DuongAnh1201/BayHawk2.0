from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.config import settings
from app.dependencies import get_current_user
from app.schemas.sweep import RegistrySweepResponse, SatelliteSweepResponse
from app.services.ai.agents.orchestrator import OrchestratorAgent
from app.services.ai.schemas.pipeline import AlertEvent, PipelineResult
from app.services.scanner import run_satellite_sweep_now, sweep_all_registered_cameras_to_db

router = APIRouter(prefix="/ai", tags=["ai"])

# Single shared orchestrator instance (agents are stateless per-call)
_orchestrator = OrchestratorAgent()


@router.post(
    "/analyze",
    response_model=PipelineResult,
    status_code=status.HTTP_200_OK,
    summary="Run the full fire-detection pipeline for a given alert event.",
)
async def analyze(
    event: AlertEvent,
    _user=Depends(get_current_user),
) -> PipelineResult:
    try:
        return await _orchestrator.run(event=event)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/sweep-cameras",
    response_model=RegistrySweepResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan every active registered camera, save results (lat/lon per row).",
    description=(
        "Loads all active rows from the ``cameras`` table, fetches one image per ``image_url``, "
        "uploads the JPEG to Supabase Storage (when configured), runs YOLO, and inserts one "
        "``scan_results`` row per camera with ``snapshot_url``, ``observed_lat`` / ``observed_lon``, "
        "and ``scan_metadata``. Optional ``trigger_focus`` runs the full pipeline for each detection."
    ),
)
async def sweep_registered_cameras(
    trigger_focus: bool = Query(
        False,
        description="If true, run focus pipeline for each camera with a positive YOLO detection.",
    ),
    _user: str = Depends(get_current_user),
) -> RegistrySweepResponse:
    if settings.database_url_async is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. Set DATABASE_URL.",
        )
    try:
        summary = await sweep_all_registered_cameras_to_db(
            trigger_focus_on_detection=trigger_focus,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return RegistrySweepResponse(
        cameras_scanned=summary.cameras_scanned,
        scan_rows_inserted=summary.scan_rows_inserted,
        detection_triggers=summary.detection_triggers,
        errors=summary.errors,
        trigger_focus_on_detection=summary.trigger_focus_on_detection,
    )


@router.post(
    "/sweep-satellite",
    response_model=SatelliteSweepResponse,
    status_code=status.HTTP_200_OK,
    summary="Run FIRMS wide-area sweep now (persist observations + focus pipelines).",
    description=(
        "Same logic as the scheduled satellite job: query NASA FIRMS for ``SCANNER_SATELLITE_BBOX``, "
        "insert ``satellite_observations`` rows, then attempt the focus pipeline once per unique "
        "hotspot cell (subject to ``FOCUS_COOLDOWN_SEC``). Does not require ``SCANNER_ENABLED``."
    ),
)
async def sweep_satellite(
    _user: str = Depends(get_current_user),
) -> SatelliteSweepResponse:
    if settings.database_url_async is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. Set DATABASE_URL.",
        )
    try:
        summary = await run_satellite_sweep_now()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return SatelliteSweepResponse(
        observations_inserted=summary.observations_inserted,
        focus_cells_considered=summary.focus_cells_considered,
        focus_pipelines_run=summary.focus_pipelines_run,
        skipped_reason=summary.skipped_reason,
        error_detail=summary.error_detail,
    )
