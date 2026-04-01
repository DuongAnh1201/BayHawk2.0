from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent, ImageUrl, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import settings
from app.services.ai.prompt.templates import REASONING_SYSTEM_PROMPT
from app.services.ai.schemas.pipeline import (
    ConfirmationStatus,
    ReasoningResult,
    SatelliteResult,
    WeatherResult,
)

from .base import BaseAgent

_MOCK_RESULT = ReasoningResult(
    scene_description=(
        "Dense smoke column rising from a steep hillside with active flame front "
        "advancing northeast. Chaparral and dry brush are primary fuel sources."
    ),
    key_observations=[
        "Active flame front moving northeast driven by Santa Ana winds",
        "Dense smoke obscuring visibility beyond 500 m",
        "Dry chaparral acting as primary fuel — high burn rate expected",
        "No visible fire breaks or natural barriers ahead of the fire front",
        "Nearest structures approximately 1.2 km from current perimeter",
    ],
)


@dataclass
class _Deps:
    weather: WeatherResult
    confirmation: ConfirmationStatus
    satellite: SatelliteResult


def _build_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        "gpt-4o",
        provider=OpenAIProvider(api_key=settings.openai_api_key),
    )


_agent: Agent[_Deps, ReasoningResult] = Agent(
    _build_model(),
    deps_type=_Deps,
    output_type=ReasoningResult,
    system_prompt=REASONING_SYSTEM_PROMPT,
)


@_agent.system_prompt
def _weather_context(ctx: RunContext[_Deps]) -> str:
    w = ctx.deps.weather
    return (
        f"Current weather: wind {w.wind_speed} m/s at {w.wind_direction}°, "
        f"humidity {w.humidity}%, spread risk {w.spread_risk:.2f}/1.0."
    )


@_agent.system_prompt
def _detection_context(ctx: RunContext[_Deps]) -> str:
    s = ctx.deps.satellite
    return (
        f"Satellite thermal data: hotspot_detected={s.hotspot_detected}, "
        f"thermal_confidence={s.thermal_confidence:.2f}. "
        f"Fusion status: {ctx.deps.confirmation.value}."
    )


class ReasoningAgent(BaseAgent):
    name = "reasoning"

    async def run(
        self,
        *,
        image_url: str | None,
        weather: WeatherResult,
        confirmation: ConfirmationStatus,
        satellite: SatelliteResult,
        **_,
    ) -> ReasoningResult:
        if settings.is_mock:
            return _MOCK_RESULT

        prompt: list = ["Analyze this wildfire scene and provide your structured observations."]
        if image_url:
            prompt.insert(0, ImageUrl(url=image_url))

        result = await _agent.run(
            prompt,
            deps=_Deps(weather=weather, confirmation=confirmation, satellite=satellite),
        )
        return result.output
