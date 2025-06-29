import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


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
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # File paths
    videos_dir: str = "./videos"
    sessions_dir: str = "./sessions"
    logs_dir: str = "./logs"

    # Selenium settings - исправляем парсинг
    chrome_options: str = "--headless,--no-sandbox,--disable-dev-shm-usage,--disable-gpu,--disable-software-rasterizer"

    # Celery settings
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    def get_allowed_origins(self) -> List[str]:
        """Get parsed CORS origins as list."""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(",")]
        return self.allowed_origins

    def get_chrome_options_list(self) -> List[str]:
        """Get Chrome options as list."""
        if isinstance(self.chrome_options, str):
            return [option.strip() for option in self.chrome_options.split(",")]
        return self.chrome_options

    def get_celery_broker_url(self) -> str:
        """Get Celery broker URL."""
        return self.celery_broker_url or self.redis_url

    def get_celery_result_backend(self) -> str:
        """Get Celery result backend URL."""
        return self.celery_result_backend or self.redis_url

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