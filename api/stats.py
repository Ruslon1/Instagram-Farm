from fastapi import APIRouter, HTTPException
from api.models import StatsResponse
from modules.database import get_database_connection
from services.task_service import TaskService

router = APIRouter()


@router.get("/", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Count active accounts
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE COALESCE(active, 1) = 1")
            active_accounts = cursor.fetchone()[0]

            # Count pending videos
            cursor.execute("SELECT COUNT(*) FROM videos WHERE COALESCE(status, 'pending') = 'pending'")
            pending_videos = cursor.fetchone()[0]

            # Count posts today
            cursor.execute('''
                           SELECT COUNT(*)
                           FROM publicationhistory
                           WHERE DATE (created_at) = DATE ('now')
                           ''')
            posts_today = cursor.fetchone()[0]

            # Count running tasks
            running_tasks_list = await TaskService.get_recent_tasks(status="running")
            running_tasks = len(running_tasks_list)

            return StatsResponse(
                active_accounts=active_accounts,
                pending_videos=pending_videos,
                posts_today=posts_today,
                running_tasks=running_tasks
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")