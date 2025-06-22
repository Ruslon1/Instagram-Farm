from pydantic import BaseModel
from typing import List, Optional

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

# Response models
class StatsResponse(BaseModel):
    active_accounts: int
    pending_videos: int
    posts_today: int
    running_tasks: int