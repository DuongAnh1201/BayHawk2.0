from __future__ import annotations

import json

import anthropic

from app.config import settings
from app.services.ai.prompt.templates import REASONING_PROMPT
from app.services.ai.schemas.pipeline import ReasoningResult, WeatherResult

from .base import BaseAgent


class ReasoningAgent(BaseAgent):
    name = "reasoning"

    def __init__(self) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def run(
        self,
        *,
        image_url: str | None,
        weather: WeatherResult,
        **_,
    ) -> ReasoningResult:
        prompt_text = REASONING_PROMPT.format(
            wind_speed=weather.wind_speed,
            wind_direction=weather.wind_direction,
            humidity=weather.humidity,
            spread_risk=weather.spread_risk,
        )

        content: list = [{"type": "text", "text": prompt_text}]
        if image_url:
            content.insert(0, {"type": "image", "source": {"type": "url", "url": image_url}})

        message = await self._client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
        )

        raw_text = message.content[0].text
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            parsed = {"scene_description": raw_text, "key_observations": []}

        return ReasoningResult(
            scene_description=parsed.get("scene_description", ""),
            key_observations=parsed.get("key_observations", []),
        )
