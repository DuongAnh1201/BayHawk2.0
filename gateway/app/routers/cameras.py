from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Camera
from app.db.session import get_db
from app.dependencies import get_current_user
from app.schemas.cameras import CameraCreate, CameraRead, CameraUpdate

router = APIRouter(prefix="/cameras", tags=["cameras"])


@router.post("", response_model=CameraRead, status_code=status.HTTP_201_CREATED)
async def create_camera(
    body: CameraCreate,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Camera:
    cam = Camera(
        name=body.name,
        lat=body.lat,
        lon=body.lon,
        image_url=body.image_url,
        is_active=True,
    )
    db.add(cam)
    await db.commit()
    await db.refresh(cam)
    return cam


@router.get("", response_model=list[CameraRead])
async def list_cameras(
    active_only: bool = False,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Camera]:
    q = select(Camera).order_by(Camera.id)
    if active_only:
        q = q.where(Camera.is_active.is_(True))
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{camera_id}", response_model=CameraRead)
async def get_camera(
    camera_id: int,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Camera:
    cam = await db.get(Camera, camera_id)
    if cam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return cam


@router.patch("/{camera_id}", response_model=CameraRead)
async def update_camera(
    camera_id: int,
    body: CameraUpdate,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Camera:
    cam = await db.get(Camera, camera_id)
    if cam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(cam, k, v)
    await db.commit()
    await db.refresh(cam)
    return cam


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: int,
    _user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    cam = await db.get(Camera, camera_id)
    if cam is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    await db.delete(cam)
    await db.commit()
