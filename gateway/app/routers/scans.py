from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import SatelliteObservation
from app.db.models import ScanResult
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.scan_data import ScanResultRead, SatelliteObservationRead, clamp_limit

router = APIRouter(prefix="/scans", tags=["scans"])


@router.get("/results", response_model=list[ScanResultRead])
async def list_scan_results(
    camera_id: int | None = Query(None, description="Filter by camera id"),
    scan_type: str | None = Query(None, description='Filter by scan_type, e.g. "routine" or "focus"'),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ScanResult]:
    lim = clamp_limit(limit)
    q = (
        select(ScanResult)
        .options(selectinload(ScanResult.camera))
        .order_by(ScanResult.created_at.desc(), ScanResult.id.desc())
        .limit(lim)
        .offset(offset)
    )
    if camera_id is not None:
        q = q.where(ScanResult.camera_id == camera_id)
    if scan_type is not None:
        q = q.where(ScanResult.scan_type == scan_type)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/results/{scan_id}", response_model=ScanResultRead)
async def get_scan_result(
    scan_id: int,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ScanResult:
    q = (
        select(ScanResult)
        .options(selectinload(ScanResult.camera))
        .where(ScanResult.id == scan_id)
    )
    result = await db.execute(q)
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan result not found")
    return row


@router.get("/satellite-observations", response_model=list[SatelliteObservationRead])
async def list_satellite_observations(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SatelliteObservation]:
    lim = clamp_limit(limit)
    q = (
        select(SatelliteObservation)
        .order_by(SatelliteObservation.created_at.desc(), SatelliteObservation.id.desc())
        .limit(lim)
        .offset(offset)
    )
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/satellite-observations/{observation_id}", response_model=SatelliteObservationRead)
async def get_satellite_observation(
    observation_id: int,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SatelliteObservation:
    row = await db.get(SatelliteObservation, observation_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found")
    return row
