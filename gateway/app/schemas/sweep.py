from pydantic import BaseModel, Field


class RegistrySweepResponse(BaseModel):
    """Result of scanning every active registered camera and writing ``scan_results`` rows."""

    cameras_scanned: int = Field(..., description="Active cameras considered in this run")
    scan_rows_inserted: int = Field(..., description="New ScanResult rows committed")
    detection_triggers: int = Field(..., description="Cameras with YOLO fire/smoke positive")
    errors: int = Field(..., description="Batch entries that failed with an exception")
    trigger_focus_on_detection: bool = Field(..., description="Whether focus pipeline was invoked for detections")


class SatelliteSweepResponse(BaseModel):
    """Result of a manual or scheduled FIRMS wide-area sweep."""

    observations_inserted: int = Field(..., description="New satellite_observations rows committed")
    focus_cells_considered: int = Field(..., description="Unique lat/lon cells (2dp) considered for focus")
    focus_pipelines_run: int = Field(..., description="Focus pipelines that completed (excludes cooldown skips)")
    skipped_reason: str | None = Field(None, description="Why the sweep did nothing (e.g. is_mock)")
    error_detail: str | None = Field(None, description="FIRMS or transport error message")
