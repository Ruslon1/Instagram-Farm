from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
from api.models import TikTokSourceCreate, TikTokSourceUpdate
from modules.database import get_database_connection

router = APIRouter()


def convert_datetime_to_string(dt_value):
    """Convert datetime to ISO string safely"""
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


@router.get("/")
async def get_tiktok_sources(theme: Optional[str] = None, active_only: bool = True):
    """Get all TikTok sources with optional filtering - returns JSON directly"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT id, theme, tiktok_username, active, last_fetch, videos_count, created_at FROM tiktok_sources WHERE 1=1"
            params = []

            if theme:
                query += " AND theme = %s"
                params.append(theme)

            if active_only:
                query += " AND active = TRUE"

            query += " ORDER BY theme, tiktok_username"

            cursor.execute(query, params)

            sources = []
            for row in cursor.fetchall():
                try:
                    source_dict = {
                        "id": row[0],
                        "theme": row[1],
                        "tiktok_username": row[2],
                        "active": bool(row[3]),
                        "last_fetch": convert_datetime_to_string(row[4]),
                        "videos_count": row[5] or 0,
                        "created_at": convert_datetime_to_string(row[6])
                    }
                    sources.append(source_dict)
                except Exception as row_error:
                    print(f"Error processing TikTok source row: {row_error}")
                    continue

            return JSONResponse(content=sources)

    except Exception as e:
        print(f"Error fetching TikTok sources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch TikTok sources: {str(e)}")


@router.post("/")
async def create_tiktok_source(source: TikTokSourceCreate):
    """Add new TikTok source"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if source already exists
            cursor.execute(
                "SELECT id FROM tiktok_sources WHERE theme = %s AND tiktok_username = %s",
                (source.theme, source.tiktok_username)
            )

            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="TikTok source already exists for this theme")

            # Insert new source
            cursor.execute('''
                INSERT INTO tiktok_sources (theme, tiktok_username, active, created_at)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                RETURNING id
            ''', (source.theme, source.tiktok_username, source.active))

            source_id = cursor.fetchone()[0]
            conn.commit()

            # Return the created source
            cursor.execute(
                "SELECT id, theme, tiktok_username, active, last_fetch, videos_count, created_at FROM tiktok_sources WHERE id = %s",
                (source_id,)
            )
            row = cursor.fetchone()

            result = {
                "id": row[0],
                "theme": row[1],
                "tiktok_username": row[2],
                "active": bool(row[3]),
                "last_fetch": convert_datetime_to_string(row[4]),
                "videos_count": row[5] or 0,
                "created_at": convert_datetime_to_string(row[6])
            }

            return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating TikTok source: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create TikTok source: {str(e)}")


@router.put("/{source_id}")
async def update_tiktok_source(source_id: int, source: TikTokSourceUpdate):
    """Update TikTok source"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if source exists
            cursor.execute("SELECT id FROM tiktok_sources WHERE id = %s", (source_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="TikTok source not found")

            # Build update query
            update_fields = []
            params = []

            if source.theme is not None:
                update_fields.append("theme = %s")
                params.append(source.theme)

            if source.tiktok_username is not None:
                update_fields.append("tiktok_username = %s")
                params.append(source.tiktok_username)

            if source.active is not None:
                update_fields.append("active = %s")
                params.append(source.active)

            if update_fields:
                query = f"UPDATE tiktok_sources SET {', '.join(update_fields)} WHERE id = %s"
                params.append(source_id)
                cursor.execute(query, params)
                conn.commit()

            # Return updated source
            cursor.execute(
                "SELECT id, theme, tiktok_username, active, last_fetch, videos_count, created_at FROM tiktok_sources WHERE id = %s",
                (source_id,)
            )
            row = cursor.fetchone()

            result = {
                "id": row[0],
                "theme": row[1],
                "tiktok_username": row[2],
                "active": bool(row[3]),
                "last_fetch": convert_datetime_to_string(row[4]),
                "videos_count": row[5] or 0,
                "created_at": convert_datetime_to_string(row[6])
            }

            return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating TikTok source: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update TikTok source: {str(e)}")


@router.delete("/{source_id}")
async def delete_tiktok_source(source_id: int):
    """Delete TikTok source"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Check if source exists
            cursor.execute("SELECT id FROM tiktok_sources WHERE id = %s", (source_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="TikTok source not found")

            # Delete the source
            cursor.execute("DELETE FROM tiktok_sources WHERE id = %s", (source_id,))
            conn.commit()

            return {"message": f"TikTok source {source_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete TikTok source: {str(e)}")


@router.get("/themes")
async def get_themes():
    """Get list of available themes"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Get themes from both accounts and tiktok_sources
            cursor.execute('''
                SELECT DISTINCT theme
                FROM (
                    SELECT theme FROM accounts
                    UNION
                    SELECT theme FROM tiktok_sources
                ) AS combined_themes
                WHERE theme IS NOT NULL
                ORDER BY theme
            ''')

            themes = [row[0] for row in cursor.fetchall() if row[0]]
            return {"themes": themes}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get themes: {str(e)}")


@router.get("/by-theme/{theme}")
async def get_sources_by_theme(theme: str):
    """Get TikTok sources for specific theme"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, theme, tiktok_username, active, last_fetch, videos_count, created_at
                FROM tiktok_sources
                WHERE theme = %s AND active = TRUE
                ORDER BY tiktok_username
            ''', (theme,))

            sources = []
            for row in cursor.fetchall():
                try:
                    source_dict = {
                        "id": row[0],
                        "theme": row[1],
                        "tiktok_username": row[2],
                        "active": bool(row[3]),
                        "last_fetch": convert_datetime_to_string(row[4]),
                        "videos_count": row[5] or 0,
                        "created_at": convert_datetime_to_string(row[6])
                    }
                    sources.append(source_dict)
                except Exception as row_error:
                    print(f"Error processing TikTok source row: {row_error}")
                    continue

            return JSONResponse(content=sources)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sources for theme: {str(e)}")


@router.post("/{source_id}/update-stats")
async def update_source_stats(source_id: int, videos_fetched: int):
    """Update source statistics after fetching"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE tiktok_sources
                SET last_fetch = CURRENT_TIMESTAMP,
                    videos_count = videos_count + %s
                WHERE id = %s
            ''', (videos_fetched, source_id))

            conn.commit()

            return {"message": f"Updated stats for source {source_id}"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update source stats: {str(e)}")