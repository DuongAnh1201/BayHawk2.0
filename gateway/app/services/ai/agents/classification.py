from __future__ import annotations

import json

import anthropic

from app.config import settings
from app.services.ai.prompt.templates import CLASSIFICATION_PROMPT
from app.services.ai.schemas.pipeline import (
    ClassificationResult,
    CriticalityLevel,
    FusionResult,
    ReasoningResult,
    WeatherResult,
)

from .base import BaseAgent


class ClassificationAgent(BaseAgent):
    name = "classification"

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def run(
        self,
        *,
        reasoning: ReasoningResult,
        weather: WeatherResult,
        fusion: FusionResult,
        **_,
    ) -> ClassificationResult:
        prompt = CLASSIFICATION_PROMPT.format(
            scene_description=reasoning.scene_description,
            key_observations=reasoning.key_observations,
            spread_risk=weather.spread_risk,
            combined_score=fusion.combined_score,
        )

        message = await self._client.messages.create(
            model="claude-opus-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = message.content[0].text
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            parsed = {"criticality": "HIGH", "score": 0.5, "reasoning": raw_text}

        return ClassificationResult(
            criticality=CriticalityLevel(parsed.get("criticality", "MEDIUM")),
            score=float(parsed.get("score", 0.5)),
            reasoning=parsed.get("reasoning", ""),
        )
