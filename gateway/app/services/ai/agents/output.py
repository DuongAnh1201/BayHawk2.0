from __future__ import annotations

import uuid

import httpx
import logfire

from app.config import settings
from app.services.ai.schemas.pipeline import (
    AlertEvent,
    ClassificationResult,
    OutputResult,
    SuggestionResult,
)

from .base import BaseAgent


class OutputAgent(BaseAgent):
    name = "output"

    async def _send_notification(
        self,
        suggestion: SuggestionResult,
        classification: ClassificationResult,
        incident_id: str,
    ) -> bool:
        if not settings.dashboard_webhook_url:
            logfire.warn("DASHBOARD_WEBHOOK_URL not configured – skipping notification")
            return False

        payload = {
            "incident_id": incident_id,
            "criticality": classification.criticality.value,
            "alert_message": suggestion.alert_message,
            "action_plan": suggestion.action_plan,
            "recommended_resources": suggestion.recommended_resources,
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(settings.dashboard_webhook_url, json=payload)
                resp.raise_for_status()
            return True
        except Exception as exc:
            logfire.error("notification failed: {error}", error=str(exc))
            return False

    async def run(
        self,
        *,
        event: AlertEvent,
        suggestion: SuggestionResult,
        classification: ClassificationResult,
        **_,
    ) -> OutputResult:
        incident_id = str(uuid.uuid4())

        with logfire.span(
            "agent.output",
            event_id=event.event_id,
            incident_id=incident_id,
            criticality=classification.criticality.value,
            is_mock=settings.is_mock,
        ):
            if settings.is_mock:
                logfire.info("output mock – skipping webhook for incident {id}", id=incident_id)
                return OutputResult(
                    notification_sent=False,
                    dashboard_updated=False,
                    incident_id=incident_id,
                    logged=True,
                )

            notification_sent = await self._send_notification(suggestion, classification, incident_id)
            logfire.info("output: incident={id} notification={sent}", id=incident_id, sent=notification_sent)
            return OutputResult(
                notification_sent=notification_sent,
                dashboard_updated=notification_sent,
                incident_id=incident_id,
                logged=True,
            )
