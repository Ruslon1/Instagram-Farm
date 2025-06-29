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

            # Count active accounts with proper NULL handling
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM accounts WHERE COALESCE(active, TRUE) = TRUE"
                )
                active_accounts = cursor.fetchone()[0] or 0
            except Exception as e:
                print(f"Error counting accounts: {e}")
                active_accounts = 0

            # Count pending videos with proper NULL handling
            try:
                cursor.execute(
                    "SELECT COUNT(*) FROM videos WHERE COALESCE(status, 'pending') = 'pending'"
                )
                pending_videos = cursor.fetchone()[0] or 0
            except Exception as e:
                print(f"Error counting videos: {e}")
                pending_videos = 0

            # Count posts today with proper date handling
            try:
                # Use PostgreSQL-compatible date function
                cursor.execute('''
                    SELECT COUNT(*)
                    FROM publicationhistory
                    WHERE created_at::date = CURRENT_DATE
                ''')
                posts_today = cursor.fetchone()[0] or 0
            except Exception as e:
                print(f"Error counting posts today: {e}")
                # Try alternative query for SQLite compatibility
                try:
                    cursor.execute('''
                        SELECT COUNT(*)
                        FROM publicationhistory
                        WHERE date(created_at) = date('now')
                    ''')
                    posts_today = cursor.fetchone()[0] or 0
                except Exception as e2:
                    print(f"Error with alternative date query: {e2}")
                    posts_today = 0

            # Count running tasks
            try:
                running_tasks_list = await TaskService.get_recent_tasks(status="running")
                running_tasks = len(running_tasks_list) if running_tasks_list else 0
            except Exception as e:
                print(f"Error counting running tasks: {e}")
                running_tasks = 0

            print(f"Stats: accounts={active_accounts}, videos={pending_videos}, posts={posts_today}, tasks={running_tasks}")

            return StatsResponse(
                active_accounts=active_accounts,
                pending_videos=pending_videos,
                posts_today=posts_today,
                running_tasks=running_tasks
            )

    except Exception as e:
        print(f"Stats API error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")