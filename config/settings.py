import os
from typing import List, Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "Instagram Bot API"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "sqlite:///./instagram_bot.db"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # External APIs
    telegram_token: str
    telegram_chat_id: str
    ms_tokens: str = ""

    # Security
    secret_key: str = "your-secret-key-change-in-production"
    api_key: Optional[str] = None

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # File paths
    videos_dir: str = "./videos"
    sessions_dir: str = "./sessions"
    logs_dir: str = "./logs"

    # Selenium settings
    chrome_options: List[str] = [
        "--headless",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--disable-software-rasterizer"
    ]

    # Celery settings
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    @validator("celery_broker_url", pre=True, always=True)
    def set_celery_broker(cls, v, values):
        return v or values.get("redis_url")

    @validator("celery_result_backend", pre=True, always=True)
    def set_celery_backend(cls, v, values):
        return v or values.get("redis_url")

    @validator("allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("ms_tokens", pre=True)
    def parse_ms_tokens(cls, v):
        if not v:
            return ""
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"


# Create global settings instance
settings = Settings()

# Create directories if they don't exist
os.makedirs(settings.videos_dir, exist_ok=True)
os.makedirs(settings.sessions_dir, exist_ok=True)
os.makedirs(settings.logs_dir, exist_ok=True)