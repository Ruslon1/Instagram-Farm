"""
Configuration utilities for flexible settings management.

This module provides centralized configuration management with environment variable
support, type-safe getters, and validation for all application settings.
"""

from typing import Any, Dict, Optional, List, Union
from config.settings import settings
import os


class ConfigManager:
    """Centralized configuration management with environment variable support.

    Provides type-safe access to configuration values with validation and
    sensible defaults. Supports environment variable overrides for all settings.
    """

    @staticmethod
    def get_env_var(key: str, default: Any = None, required: bool = False) -> Any:
        """Get environment variable with validation.

        Args:
            key: Environment variable name
            default: Default value if not set
            required: Whether to raise error if not set

        Returns:
            Environment variable value or default

        Raises:
            ValueError: If required=True and variable is not set
        """
        value = os.getenv(key, default)
        if required and value is None:
            raise ValueError(f"Required environment variable '{key}' is not set")
        return value

    @staticmethod
    def get_env_list(key: str, default: List[str] = None, separator: str = ",") -> List[str]:
        """Get environment variable as list with separator parsing.

        Args:
            key: Environment variable name
            default: Default list if not set
            separator: String separator for splitting values

        Returns:
            List of stripped, non-empty strings
        """
        value = os.getenv(key)
        if value is None:
            return default or []
        return [item.strip() for item in value.split(separator) if item.strip()]

    @staticmethod
    def get_env_bool(key: str, default: bool = False) -> bool:
        """Get environment variable as boolean with common truthy values.

        Args:
            key: Environment variable name
            default: Default boolean value

        Returns:
            True for 'true', '1', 'yes', 'on' (case insensitive), False otherwise
        """
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')

    @staticmethod
    def get_env_int(key: str, default: int = 0, min_val: int = None, max_val: int = None) -> int:
        """Get environment variable as integer with range validation.

        Args:
            key: Environment variable name
            default: Default integer value
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)

        Returns:
            Integer value clamped to min/max range, or default on error
        """
        try:
            value = int(os.getenv(key, default))
            if min_val is not None and value < min_val:
                value = min_val
            if max_val is not None and value > max_val:
                value = max_val
            return value
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_database_config() -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'url': settings.database_url,
            'type': 'sqlite' if settings.database_url.startswith('sqlite') else 'postgresql',
            'pool_size': ConfigManager.get_env_int('DB_POOL_SIZE', 5, 1, 20),
            'max_overflow': ConfigManager.get_env_int('DB_MAX_OVERFLOW', 10, 0, 50),
            'pool_timeout': ConfigManager.get_env_int('DB_POOL_TIMEOUT', 30, 10, 300)
        }

    @staticmethod
    def get_redis_config() -> Dict[str, Any]:
        """Get Redis configuration"""
        return {
            'url': settings.redis_url,
            'max_connections': ConfigManager.get_env_int('REDIS_MAX_CONNECTIONS', 20, 1, 100),
            'socket_timeout': ConfigManager.get_env_int('REDIS_SOCKET_TIMEOUT', 5, 1, 30),
            'socket_connect_timeout': ConfigManager.get_env_int('REDIS_CONNECT_TIMEOUT', 5, 1, 30)
        }

    @staticmethod
    def get_celery_config() -> Dict[str, Any]:
        """Get Celery configuration"""
        return {
            'broker_url': settings.get_celery_broker_url(),
            'result_backend': settings.get_celery_result_backend(),
            'worker_concurrency': ConfigManager.get_env_int('CELERY_WORKER_CONCURRENCY', 4, 1, 16),
            'worker_pool': os.getenv('CELERY_WORKER_POOL', 'gevent'),
            'task_time_limit': ConfigManager.get_env_int('CELERY_TASK_TIME_LIMIT', 3600, 60, 86400),
            'task_soft_time_limit': ConfigManager.get_env_int('CELERY_TASK_SOFT_TIME_LIMIT', 3300, 30, 3600)
        }

    @staticmethod
    def get_security_config() -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'api_key': settings.api_key,
            'secret_key': settings.secret_key,
            'allowed_origins': settings.get_allowed_origins(),
            'cors_max_age': ConfigManager.get_env_int('CORS_MAX_AGE', 86400, 3600, 86400),
            'rate_limit_requests': ConfigManager.get_env_int('RATE_LIMIT_REQUESTS', 100, 10, 1000),
            'rate_limit_window': ConfigManager.get_env_int('RATE_LIMIT_WINDOW', 60, 10, 3600)
        }

    @staticmethod
    def get_instagram_config() -> Dict[str, Any]:
        """Get Instagram-specific configuration"""
        return {
            'delay_range': [1, 3],  # Fixed delays for Instagram API
            'request_timeout': ConfigManager.get_env_int('INSTAGRAM_REQUEST_TIMEOUT', 30, 10, 120),
            'max_retries': ConfigManager.get_env_int('INSTAGRAM_MAX_RETRIES', 3, 1, 10),
            'retry_delay': ConfigManager.get_env_int('INSTAGRAM_RETRY_DELAY', 5, 1, 60)
        }

    @staticmethod
    def get_tiktok_config() -> Dict[str, Any]:
        """Get TikTok-specific configuration"""
        return {
            'ms_tokens': ConfigManager.get_env_list('MS_TOKENS'),
            'max_sessions': ConfigManager.get_env_int('TIKTOK_MAX_SESSIONS', 3, 1, 10),
            'videos_per_account': ConfigManager.get_env_int('TIKTOK_VIDEOS_PER_ACCOUNT', 20, 5, 100),
            'fetch_timeout': ConfigManager.get_env_int('TIKTOK_FETCH_TIMEOUT', 60, 30, 300),
            'rate_limit_delay': ConfigManager.get_env_int('TIKTOK_RATE_LIMIT_DELAY', 3, 1, 10)
        }

    @staticmethod
    def get_file_paths() -> Dict[str, str]:
        """Get file path configuration"""
        return {
            'videos_dir': settings.videos_dir,
            'sessions_dir': settings.sessions_dir,
            'logs_dir': settings.logs_dir,
            'temp_dir': os.getenv('TEMP_DIR', '/tmp'),
            'uploads_dir': os.getenv('UPLOADS_DIR', './uploads')
        }

    @staticmethod
    def get_telegram_config() -> Dict[str, Any]:
        """Get Telegram notification configuration"""
        return {
            'token': settings.telegram_token,
            'chat_id': settings.telegram_chat_id,
            'enabled': bool(settings.telegram_token and settings.telegram_chat_id),
            'retry_count': ConfigManager.get_env_int('TELEGRAM_RETRY_COUNT', 3, 1, 5),
            'timeout': ConfigManager.get_env_int('TELEGRAM_TIMEOUT', 10, 5, 30)
        }

    @staticmethod
    def validate_config() -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # Check required configurations
        if not settings.database_url:
            issues.append("Database URL is not configured")

        if not settings.redis_url:
            issues.append("Redis URL is not configured")

        # Check Telegram config
        telegram_config = ConfigManager.get_telegram_config()
        if not telegram_config['enabled']:
            issues.append("Telegram notifications are not configured (token or chat_id missing)")

        # Check file paths exist
        file_paths = ConfigManager.get_file_paths()
        for path_name, path_value in file_paths.items():
            if not os.path.exists(path_value):
                try:
                    os.makedirs(path_value, exist_ok=True)
                except Exception as e:
                    issues.append(f"Cannot create {path_name}: {path_value} - {e}")

        return issues