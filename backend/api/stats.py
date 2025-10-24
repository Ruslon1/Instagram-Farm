from fastapi import APIRouter, HTTPException
from core import count_records, get_table_stats
from modules.database import get_database_connection

router = APIRouter()


@router.get("/")
async def get_stats():
    """Get dashboard statistics with proper error handling - returns JSON directly"""

    # Default values
    stats = {
        "active_accounts": 0,
        "pending_videos": 0,
        "posts_today": 0,
        "running_tasks": 0
    }

    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Use utility functions for cleaner code
            stats["active_accounts"] = count_records('accounts', {'active': 1})
            stats["pending_videos"] = count_records('videos')
            stats["posts_today"] = count_records('publicationhistory')

            # Running tasks (simplified for now)
            stats["running_tasks"] = 0

            print(f"Final stats: {stats}")
            return stats

    except Exception as e:
        print(f"Stats error: {e}")
        import traceback
        traceback.print_exc()
        # Return default stats instead of raising error
        return stats