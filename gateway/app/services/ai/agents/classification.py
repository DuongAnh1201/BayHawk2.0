from __future__ import annotations

from dataclasses import dataclass

import logfire
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import settings
from app.services.ai.prompt.templates import CLASSIFICATION_SYSTEM_PROMPT
from app.services.ai.schemas.pipeline import (
    ClassificationResult,
    CriticalityLevel,
    FusionResult,
    ReasoningResult,
    WeatherResult,
)

from .base import BaseAgent

_MOCK_RESULT = ClassificationResult(
    criticality=CriticalityLevel.HIGH,
    score=0.82,
    reasoning="Mock: Active spread with strong winds and critically low humidity warrants HIGH classification.",
)


@dataclass
class _Deps:
    reasoning: ReasoningResult
    weather: WeatherResult
    fusion: FusionResult


def _build_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        settings.openai_model,
        provider=OpenAIProvider(api_key=settings.openai_api_key),
    )


_agent: Agent[_Deps, ClassificationResult] = Agent(
    _build_model(),
    deps_type=_Deps,
    output_type=ClassificationResult,
    system_prompt=CLASSIFICATION_SYSTEM_PROMPT,
)


@_agent.system_prompt
def _incident_context(ctx: RunContext[_Deps]) -> str:
    d = ctx.deps
    return (
        f"Scene description: {d.reasoning.scene_description}\n"
        f"Key observations: {', '.join(d.reasoning.key_observations)}\n"
        f"Weather spread risk: {d.weather.spread_risk:.2f}\n"
        f"Combined detection score: {d.fusion.combined_score:.2f}"
    )


class ClassificationAgent(BaseAgent):
    name = "classification"

    async def run(
        self,
        *,
        reasoning: ReasoningResult,
        weather: WeatherResult,
        fusion: FusionResult,
        **_,
    ) -> ClassificationResult:
        with logfire.span("agent.classification", is_mock=settings.is_mock):
            if settings.is_mock:
                logfire.info("classification mock – criticality={c}", c=_MOCK_RESULT.criticality.value)
                return _MOCK_RESULT

            result = await _agent.run(
                "Classify the criticality of this wildfire incident.",
                deps=_Deps(reasoning=reasoning, weather=weather, fusion=fusion),
            )
            return result.output
