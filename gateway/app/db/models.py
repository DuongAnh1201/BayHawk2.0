import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.user, nullable=False)


class Camera(Base):
    """Registered camera snapshot endpoints (e.g. Supabase-managed registry)."""

    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lon: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scan_results: Mapped[list["ScanResult"]] = relationship("ScanResult", back_populates="camera")


class ScanResult(Base):
    """YOLO scan history per camera (routine interval or focus). ``observed_*`` = registry lat/lon at scan time."""

    __tablename__ = "scan_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    detected: Mapped[bool] = mapped_column(Boolean, nullable=False)
    scan_type: Mapped[str] = mapped_column(String, nullable=False)  # "routine" | "focus"
    # WGS84 snapshot from the camera row when the scan ran (for dashboards / exports without join)
    observed_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    observed_lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Public Supabase Storage URL for the captured frame (same as scan_metadata.snapshot_url when set).
    snapshot_url: Mapped[str | None] = mapped_column(String, nullable=True)
    # YOLO routine/focus context: location block, image_url, model, sweep interval, timestamps (JSON).
    # Use a portable default (Postgres ``::jsonb`` breaks SQLite DDL).
    scan_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        server_default=text("'{}'"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    camera: Mapped["Camera"] = relationship("Camera", back_populates="scan_results")


class SatelliteObservation(Base):
    """One FIRMS hotspot row persisted per wide-area satellite sweep (location + payload for downstream systems)."""

    __tablename__ = "satellite_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lat: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    lon: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    frp: Mapped[float | None] = mapped_column(Float, nullable=True)
    raw: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
