# core/__init__.py
from typing import Optional, Any
from datetime import datetime

from .logging import setup_logging, get_logger
from .security import get_current_user, verify_api_key
from .database_utils import (
    get_account_by_username, account_exists, video_exists,
    get_active_accounts, get_videos_by_theme, count_records, get_table_stats
)
from .config_utils import ConfigManager


def safe_datetime_to_string(dt_value: Optional[Any]) -> Optional[str]:
    """Safely convert datetime to string with proper type hints.

    Args:
        dt_value: Value to convert (datetime, str, or None)

    Returns:
        ISO formatted string or None
    """
    if dt_value is None:
        return None
    if isinstance(dt_value, datetime):
        return dt_value.isoformat()
    if isinstance(dt_value, str):
        return dt_value
    try:
        if hasattr(dt_value, 'isoformat'):
            return dt_value.isoformat()
        return str(dt_value)
    except Exception:
        return None


__all__ = [
    "setup_logging", "get_logger", "get_current_user", "verify_api_key",
    "safe_datetime_to_string", "sanitize_input", "validate_username",
    "validate_url", "validate_theme", "validate_video_link",
    "get_account_by_username", "account_exists", "video_exists",
    "get_active_accounts", "get_videos_by_theme", "count_records", "get_table_stats",
    "ConfigManager"
]