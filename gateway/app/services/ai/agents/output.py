from __future__ import annotations

import logging
import uuid

import httpx

from app.config import settings
from app.services.ai.schemas.pipeline import (
    AlertEvent,
    ClassificationResult,
    OutputResult,
    SuggestionResult,
)

from .base import BaseAgent

logger = logging.getLogger(__name__)


class OutputAgent(BaseAgent):
    name = "output"

    async def _send_notification(
        self,
        suggestion: SuggestionResult,
        classification: ClassificationResult,
        incident_id: str,
    ) -> bool:
        if not settings.dashboard_webhook_url:
            logger.warning("DASHBOARD_WEBHOOK_URL not configured – skipping notification.")
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
            logger.error("Notification delivery failed: %s", exc)
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
        notification_sent = await self._send_notification(suggestion, classification, incident_id)

        logger.info(
            "Incident %s | event=%s | criticality=%s | notification=%s",
            incident_id,
            event.event_id,
            classification.criticality.value,
            notification_sent,
        )

        return OutputResult(
            notification_sent=notification_sent,
            dashboard_updated=notification_sent,
            incident_id=incident_id,
            logged=True,
        )
