from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Account models
class Account(BaseModel):
    username: str
    theme: str
    status: str = "active"
    posts_count: int = 0
    last_login: Optional[str] = None

class AccountCreate(BaseModel):
    username: str
    password: str
    theme: str
    two_fa_key: Optional[str] = None

# Video models
class Video(BaseModel):
    link: str
    theme: str
    status: str = "pending"
    created_at: Optional[str] = None

# TikTok Source models
class TikTokSource(BaseModel):
    id: int
    theme: str
    tiktok_username: str
    active: bool = True
    last_fetch: Optional[str] = None
    videos_count: int = 0
    created_at: str

class TikTokSourceCreate(BaseModel):
    theme: str
    tiktok_username: str
    active: bool = True

class TikTokSourceUpdate(BaseModel):
    theme: Optional[str] = None
    tiktok_username: Optional[str] = None
    active: Optional[bool] = None

# Task models
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