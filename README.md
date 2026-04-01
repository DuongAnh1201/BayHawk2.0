# BayHawk 2.0

AI-powered wildfire detection and response system. Combines live camera feeds, satellite thermal data, and weather conditions to detect fires, assess severity, and generate actionable emergency response plans.

---

## How it works

```
[ORCHESTRATOR]
      │
      ├──────────────────────────────────────┐
      │                                      │
[CAMERA AGENT]              [SATELLITE AGENT]          [WEATHER AGENT]
AlertCA API + YOLOv8        NASA FIRMS thermal          OpenWeatherMap
Returns fire confidence     Returns hotspot score       Returns spread risk
      │                                      │
      └──────────────────────────────────────┘
                            │
                     [FUSION AGENT]
                     Combines camera + thermal scores
                     → CONFIRMED or DISMISSED
                            │
               ┌────────────┴────────────┐
           Dismissed                 Confirmed
               │                         │
             Stop              [REASONING AGENT]  ← GPT-4o (PydanticAI)
                               Analyzes image + weather context
                               Returns scene description
                                         │
                              [CLASSIFICATION AGENT]  ← GPT-4o (PydanticAI)
                              LOW / MEDIUM / HIGH / CRITICAL
                                         │
                              [SUGGESTION AGENT]  ← GPT-4o (PydanticAI)
                              Action plan + alert message
                                         │
                              [OUTPUT AGENT]
                              Webhook notification + incident log
```

Stage 1 (camera, satellite, weather) runs in parallel via `asyncio.gather`. The pipeline short-circuits at fusion if evidence is insufficient.

---

## Stack

| Layer | Technology |
|---|---|
| API gateway | FastAPI |
| Multi-agent framework | PydanticAI |
| LLM | OpenAI GPT-4o |
| Fire detection | YOLOv8 (Ultralytics) |
| Camera data | AlertCA API |
| Satellite data | NASA FIRMS (VIIRS SNPP) |
| Weather data | OpenWeatherMap |
| Auth | JWT (python-jose) |
| Database | SQLAlchemy async + aiosqlite |
| Runtime | Python 3.12 |

---

## Project structure

```
BayHawk2.0/
├── gateway/
│   └── app/
│       ├── main.py                   # FastAPI app, lifespan, router mounts
│       ├── config.py                 # Settings loaded from .env
│       ├── dependencies.py           # FastAPI Depends (auth, db)
│       ├── core/
│       │   ├── auth.py               # JWT create / decode
│       │   └── security.py           # Password hashing
│       ├── db/
│       │   ├── models.py             # SQLAlchemy ORM models
│       │   └── session.py            # Async session + init_db
│       ├── routers/
│       │   ├── auth.py               # POST /auth/register, /auth/login, GET /auth/me
│       │   └── ai.py                 # POST /ai/analyze
│       └── services/ai/
│           ├── agents/
│           │   ├── base.py           # Abstract BaseAgent
│           │   ├── orchestrator.py   # Pipeline coordinator
│           │   ├── camera.py         # AlertCA + YOLOv8
│           │   ├── satellite.py      # NASA FIRMS
│           │   ├── weather.py        # OpenWeatherMap
│           │   ├── fusion.py         # Score fusion logic
│           │   ├── reasoning.py      # PydanticAI – GPT-4o scene analysis
│           │   ├── classification.py # PydanticAI – criticality scoring
│           │   ├── suggestion.py     # PydanticAI – action plan generation
│           │   └── output.py         # Webhook + incident logging
│           ├── prompt/
│           │   └── templates.py      # System prompts for PydanticAI agents
│           └── schemas/
│               └── pipeline.py       # Pydantic models for each pipeline stage
└── tests/
    ├── conftest.py                   # Shared fixtures
    └── test_pipeline.py              # Full pipeline mock tests
```

---

## Setup

**Requirements:** Python 3.12+, [uv](https://github.com/astral-sh/uv)

```bash
git clone <repo>
cd BayHawk2.0
uv sync --dev
```

Copy and fill in the environment file:

```bash
cp .env.example .env
```

```env
# Gateway
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
CORS_ORIGIN=http://localhost:3000
DATABASE_URL=sqlite+aiosqlite:///./bayhawk.db

# AI pipeline
OPENAI_API_KEY=sk-...
ALERTCA_API_KEY=...
NASA_FIRMS_MAP_KEY=...
OPENWEATHERMAP_API_KEY=...
YOLO_MODEL_PATH=models/fire_yolov8n.pt
DASHBOARD_WEBHOOK_URL=https://your-dashboard/webhook

# Set to true to bypass all external API and LLM calls
IS_MOCK=false
```

Start the server:

```bash
PYTHONPATH=gateway uvicorn app.main:app --reload
```

---

## API

All `/ai` routes require a bearer token from `/auth/login`.

### `POST /auth/register`
```json
{ "email": "user@example.com", "password": "secret" }
```

### `POST /auth/login`
```json
{ "email": "user@example.com", "password": "secret" }
```
Returns `{ "access_token": "...", "token_type": "bearer" }`

### `POST /ai/analyze`
Triggers the full detection pipeline.

```json
{
  "event_id": "evt-001",
  "lat": 34.0522,
  "lon": -118.2437,
  "camera_id": "cam-ridge-001",
  "image_url": "https://...",
  "timestamp": "2026-04-01T12:00:00Z"
}
```

Response includes results from every pipeline stage:

```json
{
  "event_id": "evt-001",
  "camera":   { "confidence": 0.87, "detected": true, ... },
  "satellite": { "thermal_confidence": 0.76, "hotspot_detected": true, ... },
  "weather":  { "wind_speed": 13.5, "spread_risk": 0.74, ... },
  "fusion":   { "status": "CONFIRMED", "combined_score": 0.83, ... },
  "reasoning": { "scene_description": "...", "key_observations": [...] },
  "classification": { "criticality": "HIGH", "score": 0.82, ... },
  "suggestion": { "action_plan": [...], "alert_message": "...", ... },
  "output":   { "notification_sent": true, "incident_id": "...", ... }
}
```

If fusion returns `DISMISSED`, fields from `reasoning` onward are `null`.

---

## Testing

Mock mode bypasses all HTTP and LLM calls — every agent returns hardcoded realistic data.

```bash
# Run all tests in mock mode
IS_MOCK=true PYTHONPATH=gateway pytest tests/ -v
```

| Test | What it covers |
|---|---|
| `test_pipeline_confirmed_full` | All 6 stages run, result fully populated |
| `test_pipeline_dismissed_stops_after_fusion` | Pipeline halts at fusion, stages 3–6 not called |
| `test_pipeline_is_mock_flag` | `IS_MOCK=true` produces valid output with no external calls |
| `test_fusion_score_boundary` | Threshold logic at 0.40, both-positive override |
| `test_weather_spread_risk_calculation` | Spread risk stays within [0, 1] |
| `test_pipeline_event_id_propagation` | `event_id` flows through unchanged |
