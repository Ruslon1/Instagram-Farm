from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from api.models import Video
from modules.database import get_database_connection

router = APIRouter()


@router.get("/", response_model=List[Video])
async def get_videos(theme: Optional[str] = None, limit: int = 100):
    """Get videos with optional theme filter - FIXED VERSION"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Исправляем параметры для PostgreSQL
            if theme:
                cursor.execute('''
                               SELECT link,
                                      theme,
                                      COALESCE(status, 'pending') as status,
                                      created_at
                               FROM videos
                               WHERE theme = %s
                               ORDER BY created_at DESC LIMIT %s
                               ''', (theme, limit))
            else:
                cursor.execute('''
                               SELECT link,
                                      theme,
                                      COALESCE(status, 'pending') as status,
                                      created_at
                               FROM videos
                               ORDER BY created_at DESC LIMIT %s
                               ''', (limit,))

            videos = []
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    try:
                        # Безопасное извлечение данных
                        link = row[0] if len(row) > 0 and row[0] else ""
                        theme_val = row[1] if len(row) > 1 and row[1] else "unknown"
                        status = row[2] if len(row) > 2 and row[2] else "pending"
                        created_at = row[3] if len(row) > 3 and row[3] else None

                        # Обработка даты
                        if created_at:
                            if hasattr(created_at, 'isoformat'):
                                created_at_str = created_at.isoformat()
                            else:
                                created_at_str = str(created_at)
                        else:
                            created_at_str = datetime.now().isoformat()

                        # Проверяем валидность данных
                        if link and theme_val:
                            videos.append(Video(
                                link=link,
                                theme=theme_val,
                                status=status,
                                created_at=created_at_str
                            ))
                    except Exception as row_error:
                        print(f"Error processing video row {row}: {row_error}")
                        continue

            print(f"✅ Successfully fetched {len(videos)} videos")
            return videos

    except Exception as e:
        print(f"❌ Error in get_videos: {e}")
        import traceback
        traceback.print_exc()

        # Возвращаем пустой список вместо ошибки для graceful degradation
        return []


@router.delete("/{video_link:path}")
async def delete_video(video_link: str):
    """Delete a specific video by link"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if video exists
            cursor.execute("SELECT link FROM videos WHERE link = %s", (video_link,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Video not found")

            # Delete the video
            cursor.execute("DELETE FROM videos WHERE link = %s", (video_link,))
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
                    # Check if video exists
                    cursor.execute("SELECT link FROM videos WHERE link = %s", (video_link,))
                    if cursor.fetchone():
                        # Delete the video
                        cursor.execute("DELETE FROM videos WHERE link = %s", (video_link,))
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
    """Delete all videos for a specific theme, optionally filtered by status"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            if status:
                # Delete videos with specific status
                cursor.execute(
                    "DELETE FROM videos WHERE theme = %s AND COALESCE(status, 'pending') = %s",
                    (theme, status)
                )
            else:
                # Delete all videos for theme
                cursor.execute("DELETE FROM videos WHERE theme = %s", (theme,))

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
                "DELETE FROM videos WHERE COALESCE(status, 'pending') = %s",
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
        valid_statuses = ['pending', 'downloaded', 'uploaded', 'failed']
        if new_status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")

        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if video exists
            cursor.execute("SELECT link FROM videos WHERE link = %s", (video_link,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Video not found")

            # Update video status
            cursor.execute(
                "UPDATE videos SET status = %s WHERE link = %s",
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

            # Get total counts by status with safe handling
            cursor.execute('''
                           SELECT COALESCE(status, 'pending') as status,
                                  COUNT(*) as count
                           FROM videos
                           GROUP BY COALESCE (status, 'pending')
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

            # Get combined stats (theme + status)
            cursor.execute('''
                           SELECT theme,
                                  COALESCE(status, 'pending') as status,
                                  COUNT(*) as count
                           FROM videos
                           WHERE theme IS NOT NULL
                           GROUP BY theme, COALESCE (status, 'pending')
                           ORDER BY theme, status
                           ''')

            combined_stats = {}
            for row in cursor.fetchall():
                if len(row) >= 3 and row[0]:
                    theme, status, count = row[0], row[1], row[2]
                    if theme not in combined_stats:
                        combined_stats[theme] = {}
                    combined_stats[theme][status] = count

            # Get total count
            cursor.execute("SELECT COUNT(*) FROM videos")
            total_result = cursor.fetchone()
            total_videos = total_result[0] if total_result else 0

            return {
                "total_videos": total_videos,
                "by_status": status_stats,
                "by_theme": theme_stats,
                "by_theme_and_status": combined_stats
            }

    except Exception as e:
        print(f"Error getting video stats: {e}")
        import traceback
        traceback.print_exc()

        # Return basic stats even if detailed query fails
        return {
            "total_videos": 0,
            "by_status": {},
            "by_theme": {},
            "by_theme_and_status": {}
        }