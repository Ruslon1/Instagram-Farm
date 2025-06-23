from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import os
import uuid

from api.models import FetchRequest, UploadRequest, TaskLog
from modules.database import get_database_connection
from modules.tasks import process_video_with_progress  # Use updated original file
from modules.fetcher import fetch_videos_for_theme_from_accounts
from services.task_service import TaskService

router = APIRouter()


@router.post("/fetch")
async def fetch_videos(request: FetchRequest):
    """Trigger video fetching from TikTok"""
    try:
        task_id = str(uuid.uuid4())

        # Log task start
        await TaskService.log_task(
            task_id=task_id,
            task_type="fetch",
            status="running",
            message=f"Fetching videos for theme {request.theme}",
            total_items=len(request.source_usernames)
        )

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

            await TaskService.log_task(
                task_id=task_id,
                task_type="fetch",
                status="success",
                message=f"Fetched {len(new_videos)} new videos for {request.theme}",
                progress=100,
                total_items=len(request.source_usernames)
            )

            return {
                "success": True,
                "task_id": task_id,
                "message": f"Fetched {len(new_videos)} new videos",
                "videos_count": len(new_videos)
            }

        except Exception as e:
            await TaskService.log_task(
                task_id=task_id,
                task_type="fetch",
                status="failed",
                message=str(e)
            )
            raise HTTPException(status_code=500, detail=f"Fetch failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start fetch task: {str(e)}")


@router.post("/upload")
async def upload_videos(request: UploadRequest):
    """Trigger video upload to Instagram with detailed progress tracking"""
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

        # Log task start with detailed info
        await TaskService.log_task(
            task_id=task_id,
            task_type="upload",
            status="running",
            account_username=request.account_username,
            message=f"Preparing to upload {len(request.video_links)} videos to @{request.account_username}",
            progress=0,
            total_items=len(request.video_links)
        )

        # Start enhanced Celery task with progress tracking
        celery_task = process_video_with_progress.delay(
            account_data,
            request.video_links,
            TELEGRAM_TOKEN,
            TELEGRAM_CHAT_ID
        )

        return {
            "success": True,
            "task_id": task_id,
            "celery_task_id": celery_task.id,
            "message": f"Upload task started for {len(request.video_links)} videos",
            "total_videos": len(request.video_links),
            "account": request.account_username
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start upload task: {str(e)}")


@router.get("/", response_model=List[TaskLog])
async def get_tasks(status: Optional[str] = None, limit: int = 50):
    """Get task logs with progress information"""
    try:
        return await TaskService.get_recent_tasks(status=status, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tasks: {str(e)}")


@router.get("/{task_id}/progress")
async def get_task_progress(task_id: str):
    """Get detailed progress for a specific task"""
    try:
        task = await TaskService.get_task_progress(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Calculate remaining time if cooldown is active
        remaining_time = None
        if task.next_action_at and task.status == "running":
            try:
                next_action = datetime.fromisoformat(task.next_action_at.replace('Z', '+00:00'))
                now = datetime.now()
                remaining_seconds = int((next_action - now).total_seconds())
                remaining_time = max(0, remaining_seconds)
            except:
                remaining_time = None

        return {
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress,
            "total_items": task.total_items,
            "current_item": task.current_item,
            "message": task.message,
            "account_username": task.account_username,
            "remaining_cooldown": remaining_time,
            "created_at": task.created_at
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task progress: {str(e)}")


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running task"""
    try:
        # Check if task exists and is running
        task = await TaskService.get_task_progress(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status != "running":
            return {"message": f"Task {task_id} is not running (status: {task.status})"}

        # Update task status to cancelled immediately
        await TaskService.update_task_status(
            task_id=task_id,
            status="cancelled",
            message="Task cancelled by user request"
        )

        # Note: The actual Celery task will check this status and stop itself
        # when it next calls check_if_cancelled()

        return {"message": f"Task {task_id} cancellation requested"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")