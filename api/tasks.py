from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import os
import uuid

from .models import FetchRequest, UploadRequest, TaskLog
from modules.database import get_database_connection
from modules.tasks import process_video
from modules.fetcher import fetch_videos_for_theme_from_accounts
from services.task_service import TaskService

router = APIRouter()


@router.post("/fetch")
async def fetch_videos(request: FetchRequest):
    """Trigger video fetching from TikTok"""
    try:
        task_id = str(uuid.uuid4())

        # Log task start
        await TaskService.log_task(task_id, "fetch", "running",
                                   message=f"Fetching videos for theme {request.theme}")

        # Run fetch in background
        try:
            new_videos = await fetch_videos_for_theme_from_accounts(
                theme=request.theme,
                fan_accounts=request.source_usernames,
                videos_per_account=request.videos_per_account
            )

            # Save new videos to database
            with get_database_connection() as conn:
                cursor = conn.cursor()
                for video_link in new_videos:
                    cursor.execute(
                        "INSERT OR IGNORE INTO videos (link, theme, status) VALUES (?, ?, 'pending')",
                        (video_link, request.theme)
                    )
                conn.commit()

            await TaskService.log_task(task_id, "fetch", "success",
                                       message=f"Fetched {len(new_videos)} new videos for {request.theme}")

            return {
                "success": True,
                "task_id": task_id,
                "message": f"Fetched {len(new_videos)} new videos",
                "videos_count": len(new_videos)
            }

        except Exception as e:
            await TaskService.log_task(task_id, "fetch", "failed", message=str(e))
            raise HTTPException(status_code=500, detail=f"Fetch failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start fetch task: {str(e)}")


@router.post("/upload")
async def upload_videos(request: UploadRequest):
    """Trigger video upload to Instagram"""
    try:
        task_id = str(uuid.uuid4())

        # Get account details
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT username, password, theme, "2FAKey" FROM accounts WHERE username = ?',
                (request.account_username,)
            )
            account_data = cursor.fetchone()

            if not account_data:
                raise HTTPException(status_code=404, detail="Account not found")

        # Get environment variables
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

        # Log task start
        await TaskService.log_task(task_id, "upload", "running",
                                   account_username=request.account_username,
                                   message=f"Starting upload of {len(request.video_links)} videos")

        # Start Celery task
        celery_task = process_video.delay(
            account_data,
            request.video_links,
            TELEGRAM_TOKEN,
            TELEGRAM_CHAT_ID
        )

        return {
            "success": True,
            "task_id": task_id,
            "celery_task_id": celery_task.id,
            "message": f"Upload task started for {len(request.video_links)} videos"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start upload task: {str(e)}")


@router.get("/", response_model=List[TaskLog])
async def get_tasks(status: Optional[str] = None, limit: int = 50):
    """Get task logs"""
    try:
        return await TaskService.get_recent_tasks(status=status, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")