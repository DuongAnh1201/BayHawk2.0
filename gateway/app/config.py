#config file for the api gateway

#All settings from environment
import os
from dotenv import load_dotenv
load_dotenv()

class Settings():
    #Gateway
    secret_key: str= os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_token_expire_minutes: str = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

    #CORS
    cors_origin: str = os.getenv("CORS_ORIGIN")

    #DATABASE
    database_url: str = os.getenv("DATABASE_URL")

    # ── AI pipeline ────────────────────────────────────────────────────────────
    # Vision-language model (OpenAI)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    
    # Camera / AlertCA
    alertca_api_key: str = os.getenv("ALERTCA_API_KEY", "")

    # Satellite / NASA FIRMS  (obtain at https://firms.modaps.eosdis.nasa.gov/api/area/)
    nasa_firms_map_key: str = os.getenv("NASA_FIRMS_MAP_KEY", "")

    # Weather / OpenWeatherMap
    openweathermap_api_key: str = os.getenv("OPENWEATHERMAP_API_KEY", "")

    # YOLOv8 model weights path (e.g. "models/fire_yolov8n.pt")
    yolo_model_path: str = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")

    # Output – webhook URL for dashboard / push notifications
    dashboard_webhook_url: str = os.getenv("DASHBOARD_WEBHOOK_URL", "")

    # Mock mode – bypasses all external API / LLM calls (for testing and local dev)
    is_mock: bool = os.getenv("IS_MOCK", "false").lower() == "true"

settings= Settings()