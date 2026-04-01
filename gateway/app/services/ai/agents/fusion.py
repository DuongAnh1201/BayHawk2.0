from app.services.ai.schemas.pipeline import (
    CameraResult,
    ConfirmationStatus,
    FusionResult,
    SatelliteResult,
)

from .base import BaseAgent

_THRESHOLD = 0.40   # combined score required for CONFIRMED


class FusionAgent(BaseAgent):
    name = "fusion"

    async def run(
        self,
        *,
        camera: CameraResult,
        satellite: SatelliteResult,
        **_,
    ) -> FusionResult:
        # Weighted combination: camera YOLOv8 60% + thermal 40%
        combined = round(camera.confidence * 0.6 + satellite.thermal_confidence * 0.4, 4)

        both_positive = camera.detected and satellite.hotspot_detected

        if combined >= _THRESHOLD or both_positive:
            status = ConfirmationStatus.CONFIRMED
            reason = (
                f"Combined score {combined:.2f} meets threshold. "
                f"Camera detected={camera.detected}, thermal hotspot={satellite.hotspot_detected}."
            )
        else:
            status = ConfirmationStatus.DISMISSED
            reason = (
                f"Combined score {combined:.2f} below threshold {_THRESHOLD}. "
                "Insufficient evidence of fire."
            )

        return FusionResult(status=status, combined_score=combined, reason=reason)
