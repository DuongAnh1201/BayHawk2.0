from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None


def _ensure_engine() -> tuple[AsyncEngine, async_sessionmaker]:
    global _engine, _session_factory
    url = settings.database_url_async
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    if _engine is None:
        _engine = create_async_engine(url, echo=False)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    assert _session_factory is not None
    return _engine, _session_factory


def get_engine() -> AsyncEngine | None:
    url = settings.database_url_async
    if not url:
        return None
    engine, _ = _ensure_engine()
    return engine


async def get_db():
    if settings.database_url_async is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured. Set DATABASE_URL.",
        )
    _, factory = _ensure_engine()
    async with factory() as session:
        yield session


@asynccontextmanager
async def async_session_scope() -> AsyncSession:
    """Background tasks (scanner). Raises if DATABASE_URL is missing."""
    if settings.database_url_async is None:
        raise RuntimeError("DATABASE_URL is not configured")
    _, factory = _ensure_engine()
    async with factory() as session:
        yield session


async def init_db() -> None:
    if settings.database_url_async is None:
        return
    from app.db.models import Base

    engine, _ = _ensure_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
