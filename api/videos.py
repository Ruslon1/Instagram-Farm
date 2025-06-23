from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from api.models import Video
from modules.database import get_database_connection

router = APIRouter()


@router.get("/", response_model=List[Video])
async def get_videos(theme: Optional[str] = None, limit: int = 100):
    """Get videos with optional theme filter"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Add status column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE videos ADD COLUMN status TEXT DEFAULT 'pending'")
                conn.commit()
            except:
                pass

            if theme:
                cursor.execute('''
                               SELECT link, theme, COALESCE(status, 'pending') as status, created_at
                               FROM videos
                               WHERE theme = ?
                               ORDER BY rowid DESC LIMIT ?
                               ''', (theme, limit))
            else:
                cursor.execute('''
                               SELECT link, theme, COALESCE(status, 'pending') as status, created_at
                               FROM videos
                               ORDER BY rowid DESC LIMIT ?
                               ''', (limit,))

            videos = []
            for row in cursor.fetchall():
                videos.append(Video(
                    link=row[0],
                    theme=row[1],
                    status=row[2],
                    created_at=row[3] or datetime.now().isoformat()
                ))

            return videos

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch videos: {str(e)}")