# config file for the api gateway

# All settings from environment
import os
from dotenv import load_dotenv

load_dotenv()


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default
    return float(raw)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default
    return raw.lower() in ("1", "true", "yes", "on")


def normalize_async_database_url(url: str | None) -> str | None:
    """Normalize DB URLs for SQLAlchemy async: Postgres → asyncpg; SQLite → aiosqlite."""
    if url is None or str(url).strip() == "":
        return None
    u = str(url).strip()
    if u.startswith("postgresql+asyncpg://"):
        return u
    if u.startswith("postgresql://"):
        return u.replace("postgresql://", "postgresql+asyncpg://", 1)
    if u.startswith("postgres://"):
        return u.replace("postgres://", "postgresql+asyncpg://", 1)
    if u.startswith("sqlite+aiosqlite://"):
        return u
    if u.startswith("sqlite://"):
        return u.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return u


class Settings:
    # Gateway
    secret_key: str = os.getenv("SECRET_KEY", "")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: str = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")

    # CORS
    cors_origin: str = os.getenv("CORS_ORIGIN", "")

    # DATABASE (Supabase Postgres — use async URL for SQLAlchemy)
    database_url: str | None = os.getenv("DATABASE_URL") or None

    # Supabase Storage — camera snapshot JPEGs (service role key for server uploads)
    supabase_url: str = os.getenv("SUPABASE_URL", "").strip()
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
    supabase_storage_bucket: str = os.getenv("SUPABASE_STORAGE_BUCKET", "snapshots").strip() or "snapshots"

    # Auth (single admin — JWT login)
    admin_email: str = os.getenv("ADMIN_EMAIL", "admin@bayhawk.com")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "")

    # Observability (Logfire)
    logfire_api_key: str = os.getenv("LOGFIRE_API_KEY", "")
    logfire_environment: str = os.getenv("LOGFIRE_ENVIRONMENT", "local")

    # ── AI pipeline ────────────────────────────────────────────────────────────
    # Vision-language model (OpenAI)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

    # Camera — ALERTCalifornia (UC San Diego), California camera network:
    #   https://alertcalifornia.org/  |  Partner API token → ALERTCA_API_KEY
    alertca_api_key: str = os.getenv("ALERTCA_API_KEY", "")

    # Satellite — NASA LANCE FIRMS Area API only (global; includes CA). Free MAP_KEY:
    #   https://firms.modaps.eosdis.nasa.gov/api/area/
    # Product layer examples: VIIRS_SNPP_NRT, VIIRS_NOAA20_NRT, MODIS_NRT (see FIRMS docs).
    nasa_firms_map_key: str = os.getenv("NASA_FIRMS_MAP_KEY", "")
    nasa_firms_source: str = os.getenv("NASA_FIRMS_SOURCE", "VIIRS_SNPP_NRT").strip() or "VIIRS_SNPP_NRT"
    # Last URL segment: days of data to include (typical 1 for NRT).
    firms_area_day_range: int = _env_int("FIRMS_AREA_DAY_RANGE", 1)

    # Weather — OpenWeatherMap current weather (lat/lon; use CA coords for CA incidents):
    #   https://openweathermap.org/api
    openweathermap_api_key: str = os.getenv("OPENWEATHERMAP_API_KEY", "")

    # YOLOv8 weights — accuracy/speed tradeoff (larger custom-trained models: better accuracy, slower).
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
    # Inference square size (pixels). Lower = faster, slightly worse small-object accuracy (typ. 320–640).
    yolo_inference_imgsz: int = _env_int("YOLO_INFERENCE_IMGSZ", 640)

    # Collection HTTP — cost/speed vs robustness (fewer attempts = lower tail latency & fewer billed retries).
    collection_http_max_attempts: int = _env_int("COLLECTION_HTTP_MAX_ATTEMPTS", 3)

    # Repeat lat/lon within TTL: skip OpenWeather + FIRMS HTTP (saves API quota & milliseconds).
    # 0 = disabled. Typical: 60–300 for dashboards polling the same incident.
    collection_cache_ttl_sec: int = _env_int("COLLECTION_CACHE_TTL_SEC", 0)

    # FIRMS bbox half-width (degrees). Larger = more context & slightly slower payloads; smaller = tighter / faster.
    firms_bbox_half_deg: float = _env_float("FIRMS_BBOX_HALF_DEG", 0.1)
    # Scale max FRP (MW) to thermal_confidence 1.0 — tune with validation data.
    firms_frp_normalize: float = _env_float("FIRMS_FRP_NORMALIZE", 100.0)

    # Fusion — accuracy vs false positives (higher threshold = fewer CONFIRMED).
    fusion_threshold: float = _env_float("FUSION_THRESHOLD", 0.40)
    # Weight on camera YOLO vs thermal (thermal weight = 1 - this). Sum implied = 1.0.
    fusion_camera_weight: float = _env_float("FUSION_CAMERA_WEIGHT", 0.6)

    # Output – webhook URL for dashboard / push notifications
    dashboard_webhook_url: str = os.getenv("DASHBOARD_WEBHOOK_URL", "")

    # Mock mode – bypasses external API / LLM calls where agents support it (local dev / tests)
    is_mock: bool = os.getenv("IS_MOCK", "false").lower() == "true"

    # ── Continuous scanner (cameras + satellite) ───────────────────────────────
    scanner_enabled: bool = _env_bool("SCANNER_ENABLED", True)
    scan_interval_sec: int = _env_int("SCAN_INTERVAL_SEC", 300)
    satellite_scan_interval_sec: int = _env_int("SATELLITE_SCAN_INTERVAL_SEC", 300)
    scan_camera_batch_size: int = _env_int("SCAN_CAMERA_BATCH_SIZE", 10)
    focus_radius_km: float = _env_float("FOCUS_RADIUS_KM", 15.0)
    # NASA FIRMS bbox for satellite sweep: west,south,east,north (decimal degrees)
    scanner_satellite_bbox: str = os.getenv(
        "SCANNER_SATELLITE_BBOX",
        "-124.5,32.5,-114.0,42.0",
    )
    # Min seconds before re-focusing the same grid cell (lat/lon rounded to 2 decimals)
    focus_cooldown_sec: int = _env_int("FOCUS_COOLDOWN_SEC", 3600)
    # Scheduled camera sweep: after each camera YOLO, run full focus pipeline on detections (see POST /ai/sweep-cameras).
    routine_triggers_focus: bool = _env_bool("SCANNER_ROUTINE_TRIGGERS_FOCUS", True)

    def __init__(self) -> None:
        w = self.fusion_camera_weight
        if not 0.05 <= w <= 0.95:
            raise ValueError("FUSION_CAMERA_WEIGHT must be between 0.05 and 0.95")
        if self.firms_frp_normalize <= 0:
            raise ValueError("FIRMS_FRP_NORMALIZE must be positive")
        if self.collection_http_max_attempts < 1:
            raise ValueError("COLLECTION_HTTP_MAX_ATTEMPTS must be >= 1")
        if self.yolo_inference_imgsz < 32:
            raise ValueError("YOLO_INFERENCE_IMGSZ must be >= 32")
        if self.scan_interval_sec < 10:
            raise ValueError("SCAN_INTERVAL_SEC must be >= 10")
        if self.satellite_scan_interval_sec < 10:
            raise ValueError("SATELLITE_SCAN_INTERVAL_SEC must be >= 10")
        if self.scan_camera_batch_size < 1:
            raise ValueError("SCAN_CAMERA_BATCH_SIZE must be >= 1")
        if self.focus_radius_km <= 0:
            raise ValueError("FOCUS_RADIUS_KM must be positive")
        if self.firms_area_day_range < 1 or self.firms_area_day_range > 10:
            raise ValueError("FIRMS_AREA_DAY_RANGE must be between 1 and 10")
        _cam_half = os.getenv("FIRMS_CAMERA_BBOX_HALF_DEG", "").strip()
        if _cam_half != "" and float(_cam_half) <= 0:
            raise ValueError("FIRMS_CAMERA_BBOX_HALF_DEG must be positive")

    @property
    def firms_camera_bbox_half_deg(self) -> float:
        """FIRMS half-width (deg) around the incident for the camera stage; defaults to ``FIRMS_BBOX_HALF_DEG``."""
        raw = os.getenv("FIRMS_CAMERA_BBOX_HALF_DEG", "").strip()
        if raw == "":
            return self.firms_bbox_half_deg
        return float(raw)

    @property
    def database_url_async(self) -> str | None:
        return normalize_async_database_url(self.database_url)


settings = Settings()
