from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from core import safe_datetime_to_string, get_videos_by_theme, video_exists, count_records

router = APIRouter()


@router.get("/")
async def get_videos(theme: Optional[str] = None, limit: int = 100):
    """Get videos - returning plain JSON to avoid Pydantic validation"""
    try:
        # Validate input
        from core import validate_theme
        if theme and not validate_theme(theme):
            raise HTTPException(status_code=400, detail="Invalid theme name")

        if limit < 1 or limit > 1000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 1000")

        # Use utility function for cleaner code
        videos_data = get_videos_by_theme(theme=theme, limit=limit)

        # Convert to the expected format
        videos = []
        for video in videos_data:
            video_dict = {
                "link": video['link'],
                "theme": video['theme'],
                "status": video['status'],
                "created_at": safe_datetime_to_string(video['created_at']) or datetime.now().isoformat()
            }
            videos.append(video_dict)

        print(f"✅ Successfully processed {len(videos)} videos")
        return JSONResponse(content=videos)

    except Exception as e:
        print(f"❌ Error in get_videos: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(content=[])


@router.delete("/{video_link:path}")
async def delete_video(video_link: str):
    """Delete a specific video by link"""
    try:
        # Validate input
        from core import validate_video_link
        if not validate_video_link(video_link):
            raise HTTPException(status_code=400, detail="Invalid video link format")

        with get_database_connection() as conn:
            cursor = conn.cursor()

            if not video_exists(video_link):
                raise HTTPException(status_code=404, detail="Video not found")

            cursor.execute("DELETE FROM videos WHERE link = ?", (video_link,))
            conn.commit()

            return {"message": f"Video deleted successfully", "deleted_link": video_link}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting video: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")


@router.post("/bulk-delete")
async def bulk_delete_videos(video_links: List[str]):
    """Delete multiple videos by their links"""
    try:
        if not video_links:
            raise HTTPException(status_code=400, detail="No video links provided")

        with get_database_connection() as conn:
            cursor = conn.cursor()

            deleted_count = 0
            not_found = []

            for video_link in video_links:
                try:
                    if video_exists(video_link):
                        cursor.execute("DELETE FROM videos WHERE link = ?", (video_link,))
                        deleted_count += 1
                    else:
                        not_found.append(video_link)
                except Exception as e:
                    print(f"Error deleting video {video_link}: {e}")
                    not_found.append(video_link)

            conn.commit()

            return {
                "message": f"Bulk delete completed",
                "deleted_count": deleted_count,
                "total_requested": len(video_links),
                "not_found": not_found
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in bulk delete: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete videos: {str(e)}")


@router.delete("/by-theme/{theme}")
async def delete_videos_by_theme(theme: str, status: Optional[str] = None):
    """Delete all videos for a specific theme"""
    try:
        # Validate input
        from core import validate_theme
        if not validate_theme(theme):
            raise HTTPException(status_code=400, detail="Invalid theme name")

        valid_statuses = ['pending', 'downloaded', 'uploaded', 'failed']
        if status and status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

        with get_database_connection() as conn:
            cursor = conn.cursor()

            if status:
                cursor.execute(
                    "DELETE FROM videos WHERE theme = ? AND COALESCE(status, 'pending') = ?",
                    (theme, status)
                )
            else:
                cursor.execute("DELETE FROM videos WHERE theme = ?", (theme,))

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count == 0:
                raise HTTPException(status_code=404, detail=f"No videos found for theme '{theme}'" + (
                    f" with status '{status}'" if status else ""))

            return {
                "message": f"Deleted {deleted_count} videos for theme '{theme}'" + (
                    f" with status '{status}'" if status else ""),
                "deleted_count": deleted_count,
                "theme": theme,
                "status_filter": status
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting by theme: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete videos by theme: {str(e)}")


@router.delete("/by-status/{status}")
async def delete_videos_by_status(status: str):
    """Delete all videos with a specific status"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM videos WHERE COALESCE(status, 'pending') = ?",
                (status,)
            )

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count == 0:
                raise HTTPException(status_code=404, detail=f"No videos found with status '{status}'")

            return {
                "message": f"Deleted {deleted_count} videos with status '{status}'",
                "deleted_count": deleted_count,
                "status": status
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting by status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete videos by status: {str(e)}")


@router.patch("/{video_link:path}/status")
async def update_video_status(video_link: str, new_status: str):
    """Update status of a specific video"""
    try:
        # Validate input
        from core import validate_video_link
        if not validate_video_link(video_link):
            raise HTTPException(status_code=400, detail="Invalid video link format")

        valid_statuses = ['pending', 'downloaded', 'uploaded', 'failed']
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

        with get_database_connection() as conn:
            cursor = conn.cursor()

            if not video_exists(video_link):
                raise HTTPException(status_code=404, detail="Video not found")

            cursor.execute(
                "UPDATE videos SET status = ? WHERE link = ?",
                (new_status, video_link)
            )
            conn.commit()

            return {
                "message": f"Video status updated to '{new_status}'",
                "video_link": video_link,
                "new_status": new_status
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update video status: {str(e)}")


@router.get("/stats")
async def get_video_stats():
    """Get video statistics by theme and status"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Get total counts by status
            cursor.execute('''
                SELECT COALESCE(status, 'pending') as status, 
                       COUNT(*) as count
                FROM videos
                GROUP BY COALESCE(status, 'pending')
                ORDER BY count DESC
            ''')

            status_stats = {}
            for row in cursor.fetchall():
                if len(row) >= 2:
                    status_stats[row[0]] = row[1]

            # Get total counts by theme
            cursor.execute('''
                SELECT theme, COUNT(*) as count
                FROM videos
                WHERE theme IS NOT NULL
                GROUP BY theme
                ORDER BY count DESC
            ''')

            theme_stats = {}
            for row in cursor.fetchall():
                if len(row) >= 2 and row[0]:
                    theme_stats[row[0]] = row[1]

            # Get combined stats
            cursor.execute('''
                SELECT theme,
                       COALESCE(status, 'pending') as status,
                       COUNT(*) as count
                FROM videos
                WHERE theme IS NOT NULL
                GROUP BY theme, COALESCE(status, 'pending')
                ORDER BY theme, status
            ''')

            combined_stats = {}
            for row in cursor.fetchall():
                if len(row) >= 3 and row[0]:
                    theme, status, count = row[0], row[1], row[2]
                    if theme not in combined_stats:
                        combined_stats[theme] = {}
                    combined_stats[theme][status] = count

            # Get total count using utility function
            total_videos = count_records('videos')

            return {
                "total_videos": total_videos,
                "by_status": status_stats,
                "by_theme": theme_stats,
                "by_theme_and_status": combined_stats
            }

    except Exception as e:
        print(f"Error getting video stats: {e}")
        return {
            "total_videos": 0,
            "by_status": {},
            "by_theme": {},
            "by_theme_and_status": {}
        }