from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config.settings import settings
from core.logging import get_logger

logger = get_logger("security")
security = HTTPBearer(auto_error=False)


async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> bool:
    """Verify API key if configured."""
    if not settings.api_key:
        # No API key configured, allow access
        return True

    if not credentials:
        logger.warning("Missing authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.api_key:
        logger.warning("Invalid API key provided", token=credentials.credentials[:10] + "...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info("API key verified successfully")
    return True


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> dict:
    """Get current user from token. For now returns default user."""
    await verify_api_key(credentials)

    return {
        "id": "default_user",
        "username": "admin",
        "is_active": True,
        "permissions": ["read", "write", "admin"]
    }


def check_permission(user: dict, required_permission: str) -> bool:
    """Check if user has required permission."""
    user_permissions = user.get("permissions", [])
    return required_permission in user_permissions or "admin" in user_permissions


class SecurityHeaders:
    """Security headers middleware."""

    @staticmethod
    def get_security_headers() -> dict:
        """Get security headers for responses."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }


def sanitize_input(value: str, max_length: int = 1000) -> str:
    """Enhanced input sanitization with better security."""
    if not value:
        return ""

    # Convert to string if not already
    if not isinstance(value, str):
        value = str(value)

    # Remove potentially dangerous characters and patterns
    dangerous_chars = ["<", ">", "\"", "'", "&", ";", "(", ")", "|", "`", "\\", "\0", "\n", "\r"]
    sanitized = value

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

    # Remove SQL injection patterns
    sql_patterns = ["--", "/*", "*/", "xp_", "sp_", "exec", "union", "select", "drop", "delete", "update", "insert"]
    for pattern in sql_patterns:
        sanitized = sanitized.replace(pattern, "")

    # Remove script tags and javascript
    sanitized = sanitized.replace("javascript:", "").replace("vbscript:", "").replace("onload=", "").replace("onerror=", "")

    # Truncate to max length
    return sanitized[:max_length].strip()


def validate_task_id(task_id: str) -> bool:
    """Validate task ID format."""
    if not task_id:
        return False

    # Basic UUID-like validation
    import re
    pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    return bool(re.match(pattern, task_id, re.IGNORECASE))


def validate_username(username: str) -> bool:
    """Validate Instagram username format with enhanced security."""
    if not username or not isinstance(username, str):
        return False

    # Sanitize first
    username = sanitize_input(username, max_length=30)

    # Instagram username rules: 1-30 chars, alphanumeric + dots/underscores, no consecutive dots/underscores
    import re
    pattern = r'^[a-zA-Z0-9](?:[a-zA-Z0-9._]*[a-zA-Z0-9])?$'
    return bool(re.match(pattern, username)) and 1 <= len(username) <= 30


def validate_url(url: str) -> bool:
    """Validate URL format with enhanced security."""
    if not url or not isinstance(url, str):
        return False

    # Sanitize first
    url = sanitize_input(url, max_length=1000)

    import re
    # More restrictive URL pattern for TikTok/Instagram URLs
    pattern = r'^https?://(?:www\.)?(?:tiktok\.com|instagram\.com|[\w.-]+\.(?:com|net|org))(?:[:\d]+)?(?:/(?:[\w/_.%-])*)?(?:\?(?:[\w&=%.%-])*)?(?:#(?:\w*))?$'
    return bool(re.match(pattern, url, re.IGNORECASE))


def validate_theme(theme: str) -> bool:
    """Validate theme name format."""
    if not theme or not isinstance(theme, str):
        return False

    # Sanitize first
    theme = sanitize_input(theme, max_length=50)

    # Theme should be alphanumeric with spaces, dashes, underscores
    import re
    pattern = r'^[a-zA-Z0-9\s_-]+$'
    return bool(re.match(pattern, theme)) and 1 <= len(theme) <= 50


def validate_video_link(video_link: str) -> bool:
    """Validate video link format."""
    if not video_link or not isinstance(video_link, str):
        return False

    # Must be a valid URL and contain video identifier
    return validate_url(video_link) and ('video/' in video_link or '/p/' in video_link)