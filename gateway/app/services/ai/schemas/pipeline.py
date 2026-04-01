from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ConfirmationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"


class CriticalityLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertEvent(BaseModel):
    event_id: str
    lat: float
    lon: float
    camera_id: Optional[str] = None
    image_url: Optional[str] = None
    timestamp: str


class CameraResult(BaseModel):
    confidence: float               # 0.0 – 1.0  fire/smoke detection confidence
    detected: bool
    image_url: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None  # wall time for this agent (for SLO / debugging)
    telemetry: Optional[Dict[str, Any]] = None


class SatelliteResult(BaseModel):
    thermal_confidence: float       # 0.0 – 1.0
    hotspot_detected: bool
    raw: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None
    telemetry: Optional[Dict[str, Any]] = None


class WeatherResult(BaseModel):
    wind_speed: float               # m/s
    wind_direction: float           # degrees
    humidity: float                 # %
    spread_risk: float              # 0.0 – 1.0 calculated heuristic
    raw: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None
    telemetry: Optional[Dict[str, Any]] = None


class FusionResult(BaseModel):
    status: ConfirmationStatus
    combined_score: float
    reason: str
    telemetry: Optional[Dict[str, Any]] = None


class ReasoningResult(BaseModel):
    scene_description: str
    key_observations: List[str]


class ClassificationResult(BaseModel):
    criticality: CriticalityLevel
    score: float
    reasoning: str


class SuggestionResult(BaseModel):
    action_plan: List[str]
    alert_message: str
    recommended_resources: List[str]


class OutputResult(BaseModel):
    notification_sent: bool
    dashboard_updated: bool
    incident_id: str
    logged: bool


class PipelineResult(BaseModel):
    event_id: str
    camera: Optional[CameraResult] = None
    satellite: Optional[SatelliteResult] = None
    weather: Optional[WeatherResult] = None
    fusion: Optional[FusionResult] = None
    reasoning: Optional[ReasoningResult] = None
    classification: Optional[ClassificationResult] = None
    suggestion: Optional[SuggestionResult] = None
    output: Optional[OutputResult] = None
    error: Optional[str] = None
