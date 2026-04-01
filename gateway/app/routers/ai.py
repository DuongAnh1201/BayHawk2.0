from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_current_user
from app.services.ai.agents.orchestrator import OrchestratorAgent
from app.services.ai.schemas.pipeline import AlertEvent, PipelineResult

router = APIRouter(prefix="/ai", tags=["ai"])

# Single shared orchestrator instance (agents are stateless per-call)
_orchestrator = OrchestratorAgent()


@router.post(
    "/analyze",
    response_model=PipelineResult,
    status_code=status.HTTP_200_OK,
    summary="Run the full fire-detection pipeline for a given alert event.",
)
async def analyze(
    event: AlertEvent,
    _user=Depends(get_current_user),
) -> PipelineResult:
    try:
        return await _orchestrator.run(event=event)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
