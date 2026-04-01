# BayHawk 2.0

AI-powered wildfire detection and response system. Combines **NASA FIRMS** thermal hotspots, periodic **YOLO** image analysis from registered cameras, weather context, and LLM agents to assess severity and produce response plans.

---

## How it works

```
                     ┌─────────────────────────────────┐
                     │  CONTINUOUS SCANNER (APScheduler) │
                     │  Every 5 min: 1 HTTP GET / camera │
                     │  → upload JPEG to Supabase Storage│
                     │  → YOLO on frozen bytes → Postgres│
                     │  (snapshot_url + scan_metadata)   │
                     └───────────┬──────────┬───────────┘
                  detection? ───┘          └──── FIRMS hotspot?
                                 │
                          [FOCUS MODE]
                   Multi-camera YOLO within radius
                          + full pipeline ↓

[ORCHESTRATOR]  ← Logfire tracing across all stages
      │
      ├─────────────────────────────────────────────┐
      │                      │                      │
[CAMERA AGENT]     [SATELLITE AGENT]        [WEATHER AGENT]
NASA FIRMS         NASA FIRMS               OpenWeatherMap
(local bbox)       (local bbox)           Wind / humidity
+ optional YOLO    VIIRS (config layer)    Spread risk
if image_url       Hotspot / FRP score
      │                      │                      │
      └──────────────────────┴──────────────────────┘
                             │
                      [FUSION AGENT]
                      camera × 0.6 + thermal × 0.4
                      → CONFIRMED or DISMISSED
                             │
              ┌──────────────┴──────────────┐
          Dismissed                     Confirmed
              │                             │
            Stop               [REASONING AGENT]  ← GPT (PydanticAI)
                               Image + weather context
                               → Scene description
                                             │
                               [CLASSIFICATION AGENT]  ← GPT (PydanticAI)
                               → LOW / MEDIUM / HIGH / CRITICAL
                                             │
                               [SUGGESTION AGENT]  ← GPT (PydanticAI)
                               → Action plan + alert message
                                             │
                               [OUTPUT AGENT]
                               → Webhook notification + incident log
```

### Routine camera sweep (every 5 minutes)

With `DATABASE_URL` + `SCANNER_ENABLED=true`, **APScheduler** runs a **camera sweep** every `SCAN_INTERVAL_SEC` (default 300s):

1. Load all **active** rows from the `cameras` table.
2. **Fetch one snapshot** from each camera's `image_url` (single download per sweep — not a continuous live stream).
3. **Upload** those bytes to **Supabase Storage** as `cam{id}_{timestamp}.jpg` (see [Supabase Storage](#supabase-storage-snapshots)).
4. Run **YOLOv8** on the same frozen bytes (temp file) for fire/smoke detection.
5. Insert a **`scan_results`** row with:
   - `confidence` / `detected` (YOLO output)
   - `observed_lat` / `observed_lon` (camera's registry coordinates at scan time)
   - `snapshot_url` — public Storage URL for the captured frame
   - `scan_metadata` — JSON with the same **location** block, source `image_url`, **`snapshot_url`**, analysis engine/model/imgsz, `sweep_interval_sec`, `captured_at`.

If `SUPABASE_URL` / `SUPABASE_SERVICE_KEY` are unset, YOLO still runs on the downloaded bytes but `snapshot_url` stays empty.

If `SCANNER_ROUTINE_TRIGGERS_FOCUS=true` (default) and YOLO detects fire/smoke, the scanner automatically enters **focus mode**.

### Focus mode

When triggered (routine detection, FIRMS hotspot, or manual API call):

1. Query all **active cameras within `FOCUS_RADIUS_KM`** of the incident.
2. Run **YOLO** on each nearby camera (batched).
3. Persist **focus** `scan_results` rows (with `snapshot_url`, `scan_metadata` including `focus_center`, `focus_radius_km`).
4. Run the **full orchestrator pipeline** (camera override + satellite + weather + fusion + reasoning + classification + suggestion + output).

### Satellite sweep

A parallel interval job polls **NASA FIRMS** over `SCANNER_SATELLITE_BBOX`, persists hotspots to `satellite_observations` (`lat`, `lon`, `frp`, `raw` JSON), and triggers **focus mode** for each new hotspot grid cell (subject to `FOCUS_COOLDOWN_SEC`). You can also run the same sweep on demand via **`POST /ai/sweep-satellite`** (JWT; does not require `SCANNER_ENABLED`).

### Pipeline stages

**Stage 1 — camera agent**

- **Default:** Queries the [NASA FIRMS Area API](https://firms.modaps.eosdis.nasa.gov/api/area/) around the event `lat`/`lon`. Both `raw` and `telemetry` include a **`location`** block (`incident_lat`, `incident_lon`, `bbox_wsen`, `focus_radius_km`, `focus_mode`).
- **With `image_url`:** Runs **YOLOv8** on the image. Location metadata uses the alert anchor (pixels aren't geocoded).

**Stage 1 — satellite agent**

- Same FIRMS Area API with configurable source / day range / bbox. Every result (success, error, cache hit) carries the same **`location`** block in `raw` and `telemetry`.

**Stage 1 — weather agent**

- OpenWeatherMap current weather. Computes `spread_risk` from wind speed and humidity.

Stage 1 runs in parallel via `asyncio.gather`. The pipeline short-circuits at fusion if evidence is insufficient. Every stage emits Logfire spans.

**`focus_radius_km` override:** Both `POST /ai/analyze` and scanner focus runs accept an optional `focus_radius_km`. When set, location metadata and multi-camera search use that radius instead of the server default.

---

## Stack

| Layer | Technology |
|---|---|
| API gateway | FastAPI |
| Multi-agent framework | PydanticAI |
| LLM | OpenAI (configurable model via `OPENAI_MODEL`) |
| Observability | Logfire (`instrument_pydantic_ai` + manual spans) |
| Thermal / hotspot (camera & satellite) | NASA FIRMS Area API (JSON) |
| Periodic vision (scanner) | YOLOv8 (Ultralytics) — 1 image per camera every 5 min |
| Weather | OpenWeatherMap |
| Auth | JWT (python-jose) + bcrypt |
| Registry & history | PostgreSQL (e.g. Supabase) + SQLAlchemy async (`asyncpg`) |
| Snapshot files | Supabase Storage (JPEG per sweep; `supabase` Python client) |
| Background jobs | APScheduler (camera sweep + satellite sweep intervals) |
| Runtime | Python 3.12+ / uv |

---

## Project structure

```
BayHawk2.0/
├── gateway/
│   └── app/
│       ├── main.py                   # FastAPI lifespan: init_db + APScheduler; `/`, `/health`
│       ├── config.py                 # All settings from .env
│       ├── dependencies.py           # get_current_user (JWT)
│       ├── db/
│       │   ├── models.py             # User, Camera, ScanResult, SatelliteObservation
│       │   └── session.py            # async engine, get_db, init_db
│       ├── core/
│       │   ├── auth.py               # JWT create / decode
│       │   └── security.py           # bcrypt hash / verify
│       ├── routers/
│       │   ├── auth.py               # POST /auth/login, GET /auth/me
│       │   ├── ai.py                 # POST /ai/analyze, sweep-cameras, sweep-satellite
│       │   ├── cameras.py            # CRUD /cameras (JWT) — scanner registry
│       │   └── scans.py              # GET /scans/results, satellite-observations (JWT)
│       ├── schemas/
│       │   ├── cameras.py            # Pydantic models for /cameras
│       │   ├── scan_data.py          # ScanResultRead, SatelliteObservationRead
│       │   └── sweep.py              # RegistrySweepResponse, SatelliteSweepResponse
│       └── services/
│           ├── scanner.py            # Routine YOLO sweeps, focus pipeline, satellite sweep
│           ├── storage.py            # Supabase Storage upload → public snapshot URL
│           ├── camera_registry_sweep.py  # Re-export of registry sweep helper
│           └── ai/
│               ├── agents/
│               │   ├── base.py
│               │   ├── orchestrator.py   # Pipeline + camera_override (focus)
│               │   ├── firms_area.py     # Shared FIRMS fetch + hotspot parsing
│               │   ├── camera.py         # FIRMS default; YOLO if image_url
│               │   ├── satellite.py      # NASA FIRMS
│               │   ├── weather.py
│               │   ├── fusion.py
│               │   ├── reasoning.py
│               │   ├── classification.py
│               │   ├── suggestion.py
│               │   ├── output.py
│               │   ├── geo_hints.py      # Haversine + stage_location_metadata
│               │   ├── http_retry.py     # Resilient HTTP with backoff
│               │   ├── collection_cache.py  # TTL cache for repeat queries
│               │   └── ttl_cache.py
│               ├── prompt/
│               │   └── templates.py
│               └── schemas/
│                   └── pipeline.py       # AlertEvent, CameraResult, SatelliteResult, …
├── gateway/tests/                        # Unit tests (agents, fusion, orchestrator, …)
└── tests/
    └── test_pipeline.py                  # Full pipeline mock tests (6 tests)
```

---

## Setup

**Requirements:** Python 3.12+, [uv](https://github.com/astral-sh/uv)

```bash
git clone <repo>
cd BayHawk2.0
uv sync --dev
```

Generate a bcrypt hash for `ADMIN_PASSWORD`:

```bash
PYTHONPATH=gateway .venv/bin/python -c \
  "from app.core.security import hash_password; print(hash_password('yourpassword'))"
```

### Environment variables

Create a `.env` file in the project root:

```env
# Gateway
SECRET_KEY=change-me-to-a-long-random-string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Auth (JWT — single admin account)
ADMIN_EMAIL=admin@bayhawk.com
ADMIN_PASSWORD=<bcrypt hash>

# Database (Postgres — camera registry, scan history, FIRMS observations)
# Tables are created on startup via SQLAlchemy create_all.
DATABASE_URL=postgresql://USER:PASS@HOST:5432/postgres

# Supabase Storage — scanner uploads each capture as a JPEG; public URL stored in DB
# Use the service_role key (server-side). Create a public bucket in the dashboard first.
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=
# Bucket name only (must match Storage → bucket name in Supabase). Default if omitted: snapshots
SUPABASE_STORAGE_BUCKET=snapshots

# AI pipeline — OpenAI (reasoning / classification / suggestion)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini

# NASA FIRMS (required for camera + satellite stages when not in mock mode)
# Register MAP_KEY: https://firms.modaps.eosdis.nasa.gov/api/area/
NASA_FIRMS_MAP_KEY=
NASA_FIRMS_SOURCE=VIIRS_SNPP_NRT
FIRMS_AREA_DAY_RANGE=1
FIRMS_BBOX_HALF_DEG=0.1
# Optional: tighter FIRMS bbox for camera stage (defaults to FIRMS_BBOX_HALF_DEG)
FIRMS_CAMERA_BBOX_HALF_DEG=
FIRMS_FRP_NORMALIZE=100.0

OPENWEATHERMAP_API_KEY=
YOLO_MODEL_PATH=models/fire_yolov8n.pt
YOLO_INFERENCE_IMGSZ=640
COLLECTION_HTTP_MAX_ATTEMPTS=3
COLLECTION_CACHE_TTL_SEC=0

FUSION_THRESHOLD=0.40
FUSION_CAMERA_WEIGHT=0.6

DASHBOARD_WEBHOOK_URL=

LOGFIRE_API_KEY=
LOGFIRE_ENVIRONMENT=local

IS_MOCK=false

# Continuous scanner (requires DATABASE_URL)
SCANNER_ENABLED=true
SCAN_INTERVAL_SEC=300                  # 5 minutes: 1 image per camera → YOLO → DB
SATELLITE_SCAN_INTERVAL_SEC=300
SCAN_CAMERA_BATCH_SIZE=10
FOCUS_RADIUS_KM=15
SCANNER_SATELLITE_BBOX=-124.5,32.5,-114.0,42.0
FOCUS_COOLDOWN_SEC=3600
SCANNER_ROUTINE_TRIGGERS_FOCUS=true    # false = YOLO-only, no auto full pipeline
```

### Supabase Storage (snapshots)

Scanner and focus-mode YOLO paths upload each captured frame to **Supabase Storage** via [`gateway/app/services/storage.py`](gateway/app/services/storage.py).

| Variable | What to put |
|---|---|
| `SUPABASE_URL` | Project URL from **Settings → API** (e.g. `https://abcdefgh.supabase.co`). |
| `SUPABASE_SERVICE_KEY` | **service_role** secret (server only — never expose in a browser app). |
| `SUPABASE_STORAGE_BUCKET` | The **bucket name** exactly as shown under **Storage** in the dashboard (default in code: `snapshots`). Not a URL — just the short name. |

**Dashboard checklist:** create a bucket (e.g. `snapshots`), mark it **public** if you want `snapshot_url` links to open without signed tokens. Object keys look like `cam{camera_id}_{UTC_timestamp}.jpg`.

**Postgres vs Storage:** table rows and `scan_metadata` live in **Postgres** (`DATABASE_URL`). The **image bytes** live in the **Storage bucket**; the DB stores the **public URL** in `scan_results.snapshot_url`.

### Start the server

```bash
PYTHONPATH=gateway .venv/bin/uvicorn app.main:app --reload
```

Or via uv (if your uv version supports project scripts):

```bash
uv run dev    # start server
uv run test   # run tests (gateway + pipeline)
```

---

## API

Interactive docs: **`/docs`** (Swagger) or **`/openapi.json`**.

| Prefix | Auth | Purpose |
|--------|------|---------|
| `GET /` | none | Service name + links to docs, OpenAPI, health |
| `GET /health` | none | Liveness `{ "status": "ok" }` |
| `/auth/*` | login body for `/login` | JWT issuance and current user |
| `/ai/*` | JWT | Pipeline, camera sweep, satellite sweep |
| `/cameras` | JWT | Camera registry CRUD |
| `/scans/*` | JWT | Read `scan_results` and `satellite_observations` |

### `GET /`

Returns JSON with `service`, `docs`, `openapi`, and `health` paths.

### `GET /health`

Returns `{ "status": "ok" }`.

### `POST /auth/login`

```json
{ "email": "admin@bayhawk.com", "password": "yourpassword" }
```

Returns `{ "access_token": "...", "token_type": "bearer" }`.

### `GET /auth/me`

Returns the email of the authenticated user.

### `POST /ai/analyze`

Runs the full detection pipeline for one event.

```json
{
  "event_id": "evt-001",
  "lat": 34.0522,
  "lon": -118.2437,
  "camera_id": "cam-ridge-001",
  "image_url": "https://...",
  "timestamp": "2026-04-01T12:00:00Z",
  "focus_radius_km": 20
}
```

| Field | Required | Description |
|---|---|---|
| `event_id` | yes | Unique event identifier |
| `lat`, `lon` | yes | WGS84 incident coordinates |
| `camera_id` | no | Correlation tag for dashboards / logs |
| `image_url` | no | If set, camera stage uses **YOLO** (skips FIRMS for that stage) |
| `timestamp` | yes | ISO 8601 UTC |
| `focus_radius_km` | no | Override `FOCUS_RADIUS_KM` for this run (location metadata + multi-camera search) |

Response includes results from every pipeline stage:

```json
{
  "event_id": "evt-001",
  "camera":         { "confidence": 0.87, "detected": true, "raw": { "location": {...} }, ... },
  "satellite":      { "thermal_confidence": 0.76, "hotspot_detected": true, "raw": { "location": {...} }, ... },
  "weather":        { "wind_speed": 13.5, "spread_risk": 0.74, ... },
  "fusion":         { "status": "CONFIRMED", "combined_score": 0.83, ... },
  "reasoning":      { "scene_description": "...", "key_observations": [...] },
  "classification": { "criticality": "HIGH", "score": 0.82, ... },
  "suggestion":     { "action_plan": [...], "alert_message": "...", ... },
  "output":         { "notification_sent": true, "incident_id": "...", ... }
}
```

If fusion returns `DISMISSED`, all fields from `reasoning` onward are `null`.

**Location metadata** (in `camera.raw.location`, `camera.telemetry.location`, `satellite.raw.location`, `satellite.telemetry.location`):

```json
{
  "incident_lat": 34.0522,
  "incident_lon": -118.2437,
  "focus_radius_km": 15.0,
  "focus_mode": "registered_cameras_within_radius_km",
  "bbox_wsen": "-118.3437,33.9522,-118.1437,34.1522"
}
```

### `POST /ai/sweep-cameras`

Query param: `trigger_focus` (default `false`). For each active camera: one download from `image_url`, optional **Supabase Storage** upload, **YOLO** on the frozen frame, then a `scan_results` row with `snapshot_url`, `observed_lat` / `observed_lon`, and `scan_metadata`. If `trigger_focus=true`, also runs the full focus pipeline for each positive detection.

Response model: **`RegistrySweepResponse`** — `cameras_scanned`, `scan_rows_inserted`, `detection_triggers`, `errors`, `trigger_focus_on_detection`.

### `POST /ai/sweep-satellite`

Runs the same FIRMS wide-area job as the scheduler: fetch hotspots for `SCANNER_SATELLITE_BBOX`, insert `satellite_observations`, then run focus pipelines for unique hotspot cells (respecting `FOCUS_COOLDOWN_SEC`). Requires **`DATABASE_URL`**. Does **not** require `SCANNER_ENABLED`.

Response model: **`SatelliteSweepResponse`** — `observations_inserted`, `focus_cells_considered`, `focus_pipelines_run`, optional `skipped_reason` (e.g. mock mode) and `error_detail`.

### `POST / GET / PATCH / DELETE /cameras`

JWT-protected CRUD for the camera registry (`name`, `lat`, `lon`, `image_url`, `is_active`). Used by the scheduled scanner and focus mode.

### `GET /scans/results`

List YOLO scan history. Query params: `camera_id`, `scan_type` (`routine` / `focus`), `limit` (1–200, default 50), `offset`. Newest first. Each item can include nested **`camera`** (registry row).

### `GET /scans/results/{scan_id}`

Single `scan_result` by id (404 if missing). Includes **`camera`** when loaded.

### `GET /scans/satellite-observations`

Paginated list of FIRMS rows from the DB: `limit`, `offset` (same bounds as above).

### `GET /scans/satellite-observations/{observation_id}`

Single `satellite_observations` row by id (404 if missing).

---

## Database tables

| Table | Purpose |
|---|---|
| `cameras` | Registered snapshot URLs + coordinates for periodic sweeps and focus |
| `scan_results` | Per-camera YOLO outcomes (`routine` or `focus`), with `observed_lat`/`observed_lon`, `snapshot_url` (Supabase Storage), and `scan_metadata` |
| `satellite_observations` | FIRMS hotspots from wide-area satellite sweeps (`lat`, `lon`, `frp`, `raw` JSON payload) |
| `users` | Optional user model (gateway auth uses env admin + JWT, not necessarily this table) |

`scan_metadata` example (routine):

```json
{
  "mode": "routine_yolo_snapshot",
  "location": { "incident_lat": 37.8, "incident_lon": -122.4, "focus_radius_km": 15.0, "focus_mode": "..." },
  "camera": { "id": 3, "name": "Ridge North" },
  "image_url": "https://cam.example.com/snapshot.jpg",
  "snapshot_url": "https://xxxx.supabase.co/storage/v1/object/public/snapshots/cam3_20260401T120500Z.jpg",
  "analysis": { "engine": "yolo", "model_path": "models/fire_yolov8n.pt", "imgsz": 640 },
  "sweep_interval_sec": 300,
  "captured_at": "2026-04-01T12:05:00Z"
}
```

Tables are auto-created on first startup (`SQLAlchemy create_all` in `init_db`). If you manage the schema yourself (e.g. Supabase SQL editor), align columns with [`gateway/app/db/models.py`](gateway/app/db/models.py).

**Existing databases — add missing columns (example):**

```sql
ALTER TABLE scan_results ADD COLUMN IF NOT EXISTS observed_lat DOUBLE PRECISION;
ALTER TABLE scan_results ADD COLUMN IF NOT EXISTS observed_lon DOUBLE PRECISION;
ALTER TABLE scan_results ADD COLUMN IF NOT EXISTS snapshot_url VARCHAR;
-- If the table already has rows, add nullable first, backfill, then set NOT NULL if needed:
ALTER TABLE scan_results ADD COLUMN IF NOT EXISTS scan_metadata JSONB DEFAULT '{}'::jsonb;
```

**Fresh PostgreSQL — full DDL (optional):** run after creating a database; skip any object that already exists.

```sql
DO $$ BEGIN
    CREATE TYPE userrole AS ENUM ('user', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR NOT NULL UNIQUE,
    hashed_password VARCHAR NOT NULL,
    role userrole NOT NULL DEFAULT 'user'::userrole
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS cameras (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    image_url VARCHAR NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scan_results (
    id SERIAL PRIMARY KEY,
    camera_id INTEGER NOT NULL REFERENCES cameras (id) ON DELETE CASCADE,
    confidence DOUBLE PRECISION NOT NULL,
    detected BOOLEAN NOT NULL,
    scan_type VARCHAR NOT NULL,
    observed_lat DOUBLE PRECISION,
    observed_lon DOUBLE PRECISION,
    snapshot_url VARCHAR,
    scan_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_scan_results_camera_id ON scan_results (camera_id);

CREATE TABLE IF NOT EXISTS satellite_observations (
    id SERIAL PRIMARY KEY,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    frp DOUBLE PRECISION,
    raw JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_satellite_observations_lat ON satellite_observations (lat);
CREATE INDEX IF NOT EXISTS ix_satellite_observations_lon ON satellite_observations (lon);
```

---

## Observability

Logfire is configured in `main.py` and traces every pipeline run end-to-end:

```
pipeline                    (event_id, lat, lon, is_mock)
  stage_1.data_collection
    agent.camera
    agent.satellite
    agent.weather
  stage_2.fusion
  stage_3.reasoning
    agent.reasoning         → pydantic_ai.* spans (real runs only)
  stage_4.classification
    agent.classification    → pydantic_ai.* spans
  stage_5.suggestion
    agent.suggestion        → pydantic_ai.* spans
  stage_6.output
    agent.output
```

Scanner spans: `scanner.camera_sweep`, `scanner.registry_camera_scan`, `scanner.satellite_sweep`, `scanner.focus`.

Mock runs appear as short `agent.*` spans with `is_mock=true` and no PydanticAI child spans where LLMs are bypassed.

---

## Testing

- **Pipeline integration:** `tests/test_pipeline.py` — full pipeline with mocked agents.
- **Gateway unit tests:** `gateway/tests/` — agents, fusion, HTTP retry, schema contracts, collection cache, etc.

```bash
IS_MOCK=true PYTHONPATH=gateway SCANNER_ENABLED=false \
  .venv/bin/pytest gateway/tests/ tests/test_pipeline.py -v
```

| Test (examples) | What it covers |
|---|---|
| `test_pipeline_confirmed_full` | All 6 stages run, result fully populated |
| `test_pipeline_dismissed_stops_after_fusion` | Pipeline halts at fusion |
| `test_pipeline_is_mock_flag` | Mock mode produces valid output |
| `test_fusion_score_boundary` | Threshold at 0.40, both-positive override |
| `test_weather_spread_risk_calculation` | Spread risk in [0, 1] |
| `test_collection_agents` | FIRMS + YOLO camera paths, satellite, weather |
| `test_collection_cache` | TTL cache for weather + satellite |
| `test_agent_schema_contract` | Camera/satellite/weather return full contract (location metadata, telemetry) |

`gateway/tests/conftest.py` sets `IS_MOCK=false` for unit tests that mock HTTP at the agent level. Pipeline tests use `IS_MOCK=true` from the command line.
