from __future__ import annotations

import json

import anthropic

from app.config import settings
from app.services.ai.prompt.templates import SUGGESTION_PROMPT
from app.services.ai.schemas.pipeline import (
    ClassificationResult,
    ReasoningResult,
    SuggestionResult,
    WeatherResult,
)

from .base import BaseAgent


class SuggestionAgent(BaseAgent):
    name = "suggestion"

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def run(
        self,
        *,
        classification: ClassificationResult,
        reasoning: ReasoningResult,
        weather: WeatherResult,
        **_,
    ) -> SuggestionResult:
        prompt = SUGGESTION_PROMPT.format(
            criticality=classification.criticality.value,
            scene_description=reasoning.scene_description,
            spread_risk=weather.spread_risk,
        )

        message = await self._client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = message.content[0].text
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            parsed = {
                "action_plan": [raw_text],
                "alert_message": raw_text,
                "recommended_resources": [],
            }

        return SuggestionResult(
            action_plan=parsed.get("action_plan", []),
            alert_message=parsed.get("alert_message", ""),
            recommended_resources=parsed.get("recommended_resources", []),
        )
