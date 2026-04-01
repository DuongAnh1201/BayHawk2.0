from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.config import settings
from app.services.ai.prompt.templates import SUGGESTION_SYSTEM_PROMPT
from app.services.ai.schemas.pipeline import (
    ClassificationResult,
    ReasoningResult,
    SuggestionResult,
    WeatherResult,
)

from .base import BaseAgent

_MOCK_RESULT = SuggestionResult(
    action_plan=[
        "Deploy two aerial tankers to the northern flank immediately",
        "Establish firebreak along Ridge Road before flame front arrives",
        "Evacuate residents within 2 km radius — use Route 18 eastbound",
        "Pre-position engine crews at the Pinecrest subdivision entrance",
        "Request mutual aid from neighboring county strike teams",
    ],
    alert_message=(
        "WILDFIRE ALERT – HIGH criticality fire detected near coordinates 34.05°N 118.25°W. "
        "Strong southwest winds driving rapid spread. Evacuation order issued for Zone A. "
        "Avoid the area. Follow emergency services instructions."
    ),
    recommended_resources=[
        "2× aerial tankers (CL-415 or similar)",
        "4× Type-1 engine crews",
        "1× bulldozer for firebreak construction",
        "Red Cross evacuation shelter at Mountain High School",
    ],
)


@dataclass
class _Deps:
    classification: ClassificationResult
    reasoning: ReasoningResult
    weather: WeatherResult


def _build_model() -> OpenAIChatModel:
    return OpenAIChatModel(
        "gpt-4o",
        provider=OpenAIProvider(api_key=settings.openai_api_key),
    )


_agent: Agent[_Deps, SuggestionResult] = Agent(
    _build_model(),
    deps_type=_Deps,
    output_type=SuggestionResult,
    system_prompt=SUGGESTION_SYSTEM_PROMPT,
)


@_agent.system_prompt
def _incident_context(ctx: RunContext[_Deps]) -> str:
    d = ctx.deps
    return (
        f"Incident criticality: {d.classification.criticality.value} "
        f"(score {d.classification.score:.2f})\n"
        f"Scene: {d.reasoning.scene_description}\n"
        f"Spread risk: {d.weather.spread_risk:.2f}, "
        f"wind {d.weather.wind_speed} m/s, humidity {d.weather.humidity}%"
    )


class SuggestionAgent(BaseAgent):
    name = "suggestion"

    async def run(
        self,
        *,
        classification: ClassificationResult,
        reasoning: ReasoningResult,
        weather: WeatherResult,
        **_,
    ) -> SuggestionResult:
        if settings.is_mock:
            return _MOCK_RESULT

        result = await _agent.run(
            "Generate the response plan and alert message for this incident.",
            deps=_Deps(classification=classification, reasoning=reasoning, weather=weather),
        )
        return result.output
