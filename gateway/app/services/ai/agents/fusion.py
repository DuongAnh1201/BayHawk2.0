from __future__ import annotations

from app.config import settings
from app.services.ai.schemas.pipeline import (
    CameraResult,
    ConfirmationStatus,
    FusionResult,
    SatelliteResult,
)

from .base import BaseAgent


class FusionAgent(BaseAgent):
    name = "fusion"

    async def run(
        self,
        *,
        camera: CameraResult,
        satellite: SatelliteResult,
        **_,
    ) -> FusionResult:
        w_cam = settings.fusion_camera_weight
        w_therm = round(1.0 - w_cam, 4)
        threshold = settings.fusion_threshold

        combined = round(
            camera.confidence * w_cam + satellite.thermal_confidence * w_therm,
            4,
        )

        both_positive = camera.detected and satellite.hotspot_detected

        if combined >= threshold or both_positive:
            status = ConfirmationStatus.CONFIRMED
            reason = (
                f"Combined score {combined:.2f} meets threshold {threshold:.2f}. "
                f"Camera detected={camera.detected}, thermal hotspot={satellite.hotspot_detected}."
            )
        else:
            status = ConfirmationStatus.DISMISSED
            reason = (
                f"Combined score {combined:.2f} below threshold {threshold:.2f}. "
                "Insufficient evidence of fire."
            )

        telemetry = {
            "fusion_threshold": threshold,
            "weight_camera": w_cam,
            "weight_thermal": w_therm,
            "both_positive_override": both_positive,
        }

        return FusionResult(status=status, combined_score=combined, reason=reason, telemetry=telemetry)
