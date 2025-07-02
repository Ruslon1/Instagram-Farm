from fastapi import APIRouter, HTTPException
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

            # Count accounts with safe result handling
            try:
                cursor.execute("SELECT COUNT(*) FROM accounts")
                result = cursor.fetchone()
                if result:
                    stats["active_accounts"] = int(result[0])
                    print(f"Active accounts: {stats['active_accounts']}")
            except Exception as e:
                print(f"Error counting accounts: {e}")

            # Count videos with safe result handling
            try:
                cursor.execute("SELECT COUNT(*) FROM videos")
                result = cursor.fetchone()
                if result:
                    stats["pending_videos"] = int(result[0])
                    print(f"Pending videos: {stats['pending_videos']}")
            except Exception as e:
                print(f"Error counting videos: {e}")

            # Count posts today with safe result handling
            try:
                cursor.execute("SELECT COUNT(*) FROM publicationhistory")
                result = cursor.fetchone()
                if result:
                    stats["posts_today"] = int(result[0])
                    print(f"Posts today: {stats['posts_today']}")
            except Exception as e:
                print(f"Error counting posts: {e}")

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