from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import os
import uuid

from api.models import FetchRequest, UploadRequest
from modules.database import get_database_connection
from modules.tasks import process_video_with_progress
from modules.fetcher import fetch_videos_for_theme_from_accounts
from services.task_service import TaskService

router = APIRouter()


def safe_datetime_to_string(dt_value):
    """Safely convert datetime to string"""
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
                inserted_count = 0

                for video_link in new_videos:
                    try:
                        cursor.execute(
                            "INSERT INTO videos (link, theme, status) VALUES (%s, %s, 'pending') ON CONFLICT (link, theme) DO NOTHING",
                            (video_link, request.theme)
                        )
                        if cursor.rowcount > 0:
                            inserted_count += 1
                    except Exception as e:
                        print(f"Error inserting video {video_link}: {e}")
                        continue

                conn.commit()

            await TaskService.log_task(
                task_id=task_id,
                task_type="fetch",
                status="success",
                message=f"Fetched {inserted_count} new videos for {request.theme}",
                progress=100,
                total_items=len(request.source_usernames)
            )

            return {
                "success": True,
                "task_id": task_id,
                "message": f"Fetched {inserted_count} new videos",
                "videos_count": inserted_count
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
    """Trigger video upload to Instagram"""
    try:
        # Get account details
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT username, password, theme, "2FAKey" FROM accounts WHERE username = %s',
                (request.account_username,)
            )
            account_data = cursor.fetchone()

            if not account_data:
                raise HTTPException(status_code=404, detail="Account not found")

        # Convert account_data to list for Celery
        account_list = [
            account_data[0],  # username
            account_data[1],  # password
            account_data[2],  # theme
            account_data[3]  # 2FAKey
        ]

        # Get environment variables
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

        if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
            raise HTTPException(status_code=500, detail="Telegram configuration missing")

        # Start Celery task
        celery_task = process_video_with_progress.delay(
            account_list,
            request.video_links,
            TELEGRAM_TOKEN,
            TELEGRAM_CHAT_ID
        )

        return {
            "success": True,
            "task_id": celery_task.id,
            "celery_task_id": celery_task.id,
            "message": f"Upload task started for {len(request.video_links)} videos",
            "total_videos": len(request.video_links),
            "account": request.account_username
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start upload task: {str(e)}")


@router.get("/")
async def get_tasks(status: Optional[str] = None, limit: int = 50):
    """Get task logs - returning plain JSON to avoid Pydantic validation"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            if status:
                cursor.execute('''
                               SELECT id,
                                      task_type,
                                      status,
                                      account_username,
                                      message,
                                      created_at,
                                      progress,
                                      total_items,
                                      current_item,
                                      next_action_at,
                                      cooldown_seconds
                               FROM task_logs
                               WHERE status = %s
                               ORDER BY created_at DESC
                                   LIMIT %s
                               ''', (status, limit))
            else:
                cursor.execute('''
                               SELECT id,
                                      task_type,
                                      status,
                                      account_username,
                                      message,
                                      created_at,
                                      progress,
                                      total_items,
                                      current_item,
                                      next_action_at,
                                      cooldown_seconds
                               FROM task_logs
                               ORDER BY created_at DESC
                                   LIMIT %s
                               ''', (limit,))

            tasks = []
            rows = cursor.fetchall()

            print(f"✅ Fetched {len(rows)} task rows from database")

            for i, row in enumerate(rows):
                try:
                    # Безопасное извлечение данных с конвертацией datetime
                    task_dict = {
                        "id": row[0] if len(row) > 0 else "",
                        "task_type": row[1] if len(row) > 1 else "",
                        "status": row[2] if len(row) > 2 else "",
                        "account_username": row[3] if len(row) > 3 else None,
                        "message": row[4] if len(row) > 4 else None,
                        "created_at": safe_datetime_to_string(row[5]) if len(row) > 5 else datetime.now().isoformat(),
                        "progress": row[6] if len(row) > 6 else 0,
                        "total_items": row[7] if len(row) > 7 else 0,
                        "current_item": row[8] if len(row) > 8 else None,
                        "next_action_at": safe_datetime_to_string(row[9]) if len(row) > 9 else None,
                        "cooldown_seconds": row[10] if len(row) > 10 else None
                    }

                    tasks.append(task_dict)

                except Exception as row_error:
                    print(f"❌ Error processing task row {i}: {row_error}")
                    continue

            print(f"✅ Successfully processed {len(tasks)} tasks")
            return JSONResponse(content=tasks)

    except Exception as e:
        print(f"❌ Error in get_tasks: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content=[])


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
                if 'T' in task.next_action_at:
                    next_action = datetime.fromisoformat(task.next_action_at.replace('Z', '+00:00'))
                else:
                    next_action = datetime.strptime(task.next_action_at, '%Y-%m-%d %H:%M:%S')

                now = datetime.now()
                remaining_seconds = int((next_action - now).total_seconds())
                remaining_time = max(0, remaining_seconds)
            except Exception as dt_error:
                print(f"Error parsing datetime {task.next_action_at}: {dt_error}")
                remaining_time = None

        return {
            "task_id": task.id,
            "status": task.status,
            "progress": task.progress or 0,
            "total_items": task.total_items or 0,
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
        task = await TaskService.get_task_progress(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status != "running":
            return {"message": f"Task {task_id} is not running (status: {task.status})"}

        await TaskService.update_task_status(
            task_id=task_id,
            status="cancelled",
            message="Task cancelled by user request"
        )

        try:
            from celery_app import app as celery_app
            celery_app.control.revoke(task_id, terminate=True)
            print(f"Celery task {task_id} revoked")
        except Exception as celery_error:
            print(f"Could not revoke Celery task {task_id}: {celery_error}")

        return {"message": f"Task {task_id} cancellation requested"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel task: {str(e)}")


@router.delete("/{task_id}")
async def delete_task(task_id: str):
    """Delete a task from the database"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT id FROM task_logs WHERE id = %s", (task_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Task not found")

            cursor.execute("DELETE FROM task_logs WHERE id = %s", (task_id,))
            conn.commit()

            return {"message": f"Task {task_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_tasks():
    """Clean up old completed tasks"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                           DELETE
                           FROM task_logs
                           WHERE status IN ('success', 'failed', 'cancelled')
                             AND created_at < NOW() - INTERVAL '7 days'
                           ''')

            deleted_count = cursor.rowcount
            conn.commit()

            return {
                "message": f"Cleaned up {deleted_count} old tasks",
                "deleted_count": deleted_count
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup tasks: {str(e)}")


@router.get("/stats")
async def get_task_stats():
    """Get task statistics"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Get task counts by status
            cursor.execute('''
                           SELECT status, COUNT(*) as count
                           FROM task_logs
                           GROUP BY status
                           ORDER BY count DESC
                           ''')

            status_stats = {row[0]: row[1] for row in cursor.fetchall()}

            # Get task counts by type
            cursor.execute('''
                           SELECT task_type, COUNT(*) as count
                           FROM task_logs
                           GROUP BY task_type
                           ORDER BY count DESC
                           ''')

            type_stats = {row[0]: row[1] for row in cursor.fetchall()}

            # Get recent task counts (last 24 hours)
            cursor.execute('''
                           SELECT COUNT(*) as count
                           FROM task_logs
                           WHERE created_at > NOW() - INTERVAL '24 hours'
                           ''')

            recent_count = cursor.fetchone()[0]

            # Get running tasks count
            cursor.execute('''
                           SELECT COUNT(*) as count
                           FROM task_logs
                           WHERE status = 'running'
                           ''')

            running_count = cursor.fetchone()[0]

            return {
                "total_tasks": sum(status_stats.values()),
                "running_tasks": running_count,
                "recent_tasks_24h": recent_count,
                "by_status": status_stats,
                "by_type": type_stats
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get task stats: {str(e)}")