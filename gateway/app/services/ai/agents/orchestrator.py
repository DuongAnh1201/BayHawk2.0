from __future__ import annotations

import asyncio
import logging

import logfire

from app.config import settings
from app.services.ai.schemas.pipeline import (
    AlertEvent,
    CameraResult,
    ConfirmationStatus,
    PipelineResult,
    SatelliteResult,
    WeatherResult,
)

from .base import BaseAgent
from .camera import CameraAgent
from .classification import ClassificationAgent
from .fusion import FusionAgent
from .output import OutputAgent
from .reasoning import ReasoningAgent
from .satellite import SatelliteAgent
from .suggestion import SuggestionAgent
from .weather import WeatherAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    def __init__(self) -> None:
        self.camera = CameraAgent()
        self.satellite = SatelliteAgent()
        self.weather = WeatherAgent()
        self.fusion = FusionAgent()
        self.reasoning = ReasoningAgent()
        self.classification = ClassificationAgent()
        self.suggestion = SuggestionAgent()
        self.output = OutputAgent()

    async def run(
        self,
        *,
        event: AlertEvent,
        camera_override: CameraResult | None = None,
        **_,
    ) -> PipelineResult:
        result = PipelineResult(event_id=event.event_id)
        coords = {"lat": event.lat, "lon": event.lon}

        with logfire.span(
            "pipeline",
            event_id=event.event_id,
            lat=event.lat,
            lon=event.lon,
            is_mock=settings.is_mock,
            focus_multi=camera_override is not None,
        ):
            # ── Stage 1: parallel data collection ─────────────────────────────
            with logfire.span("stage_1.data_collection"):
                fr = event.focus_radius_km
                if camera_override is not None:
                    camera_res = camera_override
                    gather_out = await asyncio.gather(
                        self.satellite.run(**coords, focus_radius_km=fr),
                        self.weather.run(**coords),
                        return_exceptions=True,
                    )
                    satellite_res, weather_res = gather_out
                else:
                    gather_out = await asyncio.gather(
                        self.camera.run(**coords, image_url=event.image_url, focus_radius_km=fr),
                        self.satellite.run(**coords, focus_radius_km=fr),
                        self.weather.run(**coords),
                        return_exceptions=True,
                    )
                    camera_res, satellite_res, weather_res = gather_out

                for exc in (camera_res, satellite_res, weather_res):
                    if isinstance(exc, asyncio.CancelledError):
                        raise exc

                if isinstance(camera_res, BaseException):
                    logger.exception("[%s] Camera agent raised; using empty result", event.event_id, exc_info=camera_res)
                    camera_res = CameraResult(
                        confidence=0.0,
                        detected=False,
                        image_url=None,
                        raw={"error": "agent_exception", "detail": repr(camera_res)},
                    )
                if isinstance(satellite_res, BaseException):
                    logger.exception("[%s] Satellite agent raised; using empty result", event.event_id, exc_info=satellite_res)
                    satellite_res = SatelliteResult(
                        thermal_confidence=0.0,
                        hotspot_detected=False,
                        raw={"error": "agent_exception", "detail": repr(satellite_res)},
                    )
                if isinstance(weather_res, BaseException):
                    logger.exception("[%s] Weather agent raised; using empty result", event.event_id, exc_info=weather_res)
                    weather_res = WeatherResult(
                        wind_speed=0.0,
                        wind_direction=0.0,
                        humidity=0.0,
                        spread_risk=0.0,
                        raw={"error": "agent_exception", "detail": repr(weather_res)},
                    )

            result.camera = camera_res
            result.satellite = satellite_res
            result.weather = weather_res

            # ── Stage 2: fusion ───────────────────────────────────────────────
            with logfire.span("stage_2.fusion"):
                fusion_res = await self.fusion.run(camera=camera_res, satellite=satellite_res)
            result.fusion = fusion_res

            logfire.info(
                "fusion: {status} (score={score})",
                status=fusion_res.status.value,
                score=fusion_res.combined_score,
            )

            if fusion_res.status == ConfirmationStatus.DISMISSED:
                logfire.info("pipeline dismissed – stopping early")
                return result

            # ── Stage 3: reasoning ────────────────────────────────────────────
            with logfire.span("stage_3.reasoning"):
                reasoning_res = await self.reasoning.run(
                    image_url=event.image_url,
                    weather=weather_res,
                    confirmation=fusion_res.status,
                    satellite=satellite_res,
                )
            result.reasoning = reasoning_res

            # ── Stage 4: classification ───────────────────────────────────────
            with logfire.span("stage_4.classification"):
                classification_res = await self.classification.run(
                    reasoning=reasoning_res,
                    weather=weather_res,
                    fusion=fusion_res,
                )
            result.classification = classification_res

            # ── Stage 5: suggestion ───────────────────────────────────────────
            with logfire.span("stage_5.suggestion"):
                suggestion_res = await self.suggestion.run(
                    classification=classification_res,
                    reasoning=reasoning_res,
                    weather=weather_res,
                )
            result.suggestion = suggestion_res

            # ── Stage 6: output ───────────────────────────────────────────────
            with logfire.span("stage_6.output"):
                output_res = await self.output.run(
                    event=event,
                    suggestion=suggestion_res,
                    classification=classification_res,
                )
            result.output = output_res

            logfire.info(
                "pipeline complete – criticality={criticality} incident={incident_id}",
                criticality=classification_res.criticality.value,
                incident_id=output_res.incident_id,
            )

        return result
