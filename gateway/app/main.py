import asyncio
import logging
from contextlib import asynccontextmanager

import logfire
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI

from app.config import settings
from app.db.session import init_db
from app.routers.ai import router as ai_router
from app.routers.auth import router as auth_router
from app.routers.cameras import router as cameras_router
from app.routers.scans import router as scans_router
from app.services.scanner import ScannerService

logger = logging.getLogger(__name__)

logfire.configure(
    token=settings.logfire_api_key or None,
    service_name="bayhawk-gateway",
    environment=settings.logfire_environment,
)
logfire.instrument_pydantic_ai()  # auto-instruments reasoning / classification / suggestion


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    scheduler: AsyncIOScheduler | None = None
    if settings.scanner_enabled and settings.database_url_async is not None:
        scanner_svc = ScannerService()
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            scanner_svc.camera_sweep,
            "interval",
            seconds=settings.scan_interval_sec,
            id="bayhawk_camera_sweep",
            max_instances=1,
            coalesce=True,
        )
        scheduler.add_job(
            scanner_svc.satellite_sweep,
            "interval",
            seconds=settings.satellite_scan_interval_sec,
            id="bayhawk_satellite_sweep",
            max_instances=1,
            coalesce=True,
        )
        scheduler.start()

        async def _initial_sweeps() -> None:
            try:
                await scanner_svc.camera_sweep()
                await scanner_svc.satellite_sweep()
            except Exception:
                logger.exception("initial scanner sweep failed")

        asyncio.create_task(_initial_sweeps())
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title="BayHawk API Gateway",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "JWT login and current user"},
        {"name": "ai", "description": "Pipeline, camera registry sweep, satellite FIRMS sweep"},
        {"name": "cameras", "description": "Camera registry CRUD"},
        {"name": "scans", "description": "Scan history and FIRMS observation records"},
        {"name": "health", "description": "Liveness"},
    ],
)

app.include_router(auth_router)
app.include_router(ai_router)
app.include_router(cameras_router)
app.include_router(scans_router)


@app.get("/", tags=["health"])
async def root():
    return {
        "service": "bayhawk-gateway",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
    }


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
