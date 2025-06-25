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
    """Basic input sanitization."""
    if not value:
        return ""

    # Remove potentially dangerous characters
    dangerous_chars = ["<", ">", "\"", "'", "&", ";", "(", ")", "|", "`"]
    sanitized = value

    for char in dangerous_chars:
        sanitized = sanitized.replace(char, "")

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
    """Validate Instagram username format."""
    if not username:
        return False

    # Instagram username rules: 1-30 chars, alphanumeric + dots/underscores
    import re
    pattern = r'^[a-zA-Z0-9._]{1,30}$'
    return bool(re.match(pattern, username))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    if not url:
        return False

    import re
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?$'
    return bool(re.match(pattern, url))