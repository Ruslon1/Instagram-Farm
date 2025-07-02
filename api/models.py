from pydantic import BaseModel, field_validator
from typing import List, Optional, Union
from datetime import datetime

# Account models
class Account(BaseModel):
    username: str
    theme: str
    status: str = "active"
    posts_count: int = 0
    last_login: Optional[str] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_status: Optional[str] = None
    proxy_active: bool = False

class AccountCreate(BaseModel):
    username: str
    password: str
    theme: str
    two_fa_key: Optional[str] = None

# Proxy models
class ProxySettings(BaseModel):
    proxy_type: str = "HTTP"  # HTTP, SOCKS5
    proxy_host: str
    proxy_port: int
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    proxy_active: bool = True

class ProxyTestResult(BaseModel):
    success: bool
    message: str
    response_time: Optional[float] = None
    external_ip: Optional[str] = None

class ProxyUpdate(BaseModel):
    proxy_type: Optional[str] = None
    proxy_host: Optional[str] = None
    proxy_port: Optional[int] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    proxy_active: Optional[bool] = None

# Video models - ИСПРАВЛЕНО для datetime
class Video(BaseModel):
    link: str
    theme: str
    status: str = "pending"
    created_at: Optional[str] = None

    @field_validator('created_at', mode='before')
    @classmethod
    def validate_created_at(cls, v):
        """Convert datetime objects to ISO string"""
        if v is None:
            return datetime.now().isoformat()
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, str):
            return v
        # Try to convert other types to datetime first
        try:
            if hasattr(v, 'isoformat'):
                return v.isoformat()
            return str(v)
        except Exception:
            return datetime.now().isoformat()

# TikTok Source models
class TikTokSource(BaseModel):
    id: int
    theme: str
    tiktok_username: str
    active: bool = True
    last_fetch: Optional[str] = None
    videos_count: int = 0
    created_at: str

    @field_validator('last_fetch', 'created_at', mode='before')
    @classmethod
    def validate_datetime_fields(cls, v):
        """Convert datetime objects to ISO string"""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, str):
            return v
        try:
            if hasattr(v, 'isoformat'):
                return v.isoformat()
            return str(v)
        except Exception:
            return None

class TikTokSourceCreate(BaseModel):
    theme: str
    tiktok_username: str
    active: bool = True

class TikTokSourceUpdate(BaseModel):
    theme: Optional[str] = None
    tiktok_username: Optional[str] = None
    active: Optional[bool] = None

# Task models - ИСПРАВЛЕНО для datetime
class FetchRequest(BaseModel):
    theme: str
    source_usernames: List[str]
    videos_per_account: int = 10

class UploadRequest(BaseModel):
    account_username: str
    video_links: List[str]

class TaskLog(BaseModel):
    id: str
    task_type: str
    status: str
    created_at: str
    account_username: Optional[str] = None
    message: Optional[str] = None
    progress: Optional[int] = None
    total_items: Optional[int] = None
    current_item: Optional[str] = None
    next_action_at: Optional[str] = None
    cooldown_seconds: Optional[int] = None

    @field_validator('created_at', 'next_action_at', mode='before')
    @classmethod
    def validate_datetime_fields(cls, v):
        """Convert datetime objects to ISO string"""
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        if isinstance(v, str):
            return v
        try:
            if hasattr(v, 'isoformat'):
                return v.isoformat()
            return str(v)
        except Exception:
            return datetime.now().isoformat() if v else None

# Response models
class StatsResponse(BaseModel):
    active_accounts: int
    pending_videos: int
    posts_today: int
    running_tasks: int

# Upload progress response
class UploadProgress(BaseModel):
    task_id: str
    account_username: str
    current_video: str
    progress: int
    total_videos: int
    status: str
    message: str
    next_upload_in: Optional[int] = None  # seconds until next upload