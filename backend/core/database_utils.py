"""
Database utility functions to reduce code duplication.

This module provides centralized database operations used across the application
to eliminate repetitive query code and ensure consistent error handling.
"""

from typing import List, Dict, Any, Optional, Tuple, Union
from modules.database import get_database_connection
from core.logging import get_logger

logger = get_logger("database_utils")


def get_account_by_username(username: str) -> Optional[Tuple[str, str, str, Optional[str], str, int, int, Optional[str]]]:
    """Get complete account data by username.

    Returns a tuple containing:
    (username, password, theme, 2fa_key, status, active, posts_count, last_login)

    Args:
        username: Instagram account username

    Returns:
        Account data tuple or None if not found
    """
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT username, password, theme, "2FAKey", status, active, posts_count, last_login FROM accounts WHERE username = ?',
                (username,)
            )
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting account {username}: {e}")
        return None


def account_exists(username: str) -> bool:
    """Check if an Instagram account exists in the database.

    Args:
        username: Instagram account username to check

    Returns:
        True if account exists, False otherwise
    """
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM accounts WHERE username = ?", (username,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking account existence {username}: {e}")
        return False


def video_exists(video_link: str) -> bool:
    """Check if a video exists in the database by its link.

    Args:
        video_link: Full TikTok video URL to check

    Returns:
        True if video exists, False otherwise
    """
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM videos WHERE link = ?", (video_link,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking video existence {video_link}: {e}")
        return False


def get_active_accounts() -> List[Dict[str, Any]]:
    """Get all active Instagram accounts with complete data including proxy settings.

    Returns a list of dictionaries containing all account information needed for
    upload operations, including credentials, themes, and proxy configurations.

    Returns:
        List of account dictionaries with all necessary fields
    """
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT username, password, theme, "2FAKey", status, posts_count, last_login,
                       proxy_host, proxy_port, proxy_username, proxy_password, proxy_type,
                       proxy_active, proxy_status, proxy_last_check
                FROM accounts
                WHERE COALESCE(active, 1) = 1
                ORDER BY username
            ''')

            accounts = []
            for row in cursor.fetchall():
                accounts.append({
                    'username': row[0],
                    'password': row[1],
                    'theme': row[2],
                    'two_fa_key': row[3],
                    'status': row[4] or 'active',
                    'posts_count': row[5] or 0,
                    'last_login': row[6],
                    'proxy_host': row[7],
                    'proxy_port': row[8],
                    'proxy_username': row[9],
                    'proxy_password': row[10],
                    'proxy_type': row[11] or 'HTTP',
                    'proxy_active': bool(row[12]) if row[12] is not None else False,
                    'proxy_status': row[13] or 'unchecked',
                    'proxy_last_check': row[14]
                })
            return accounts
    except Exception as e:
        logger.error(f"Error getting active accounts: {e}")
        return []


def get_videos_by_theme(theme: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Get videos from database with optional filtering by theme and status.

    Args:
        theme: Optional theme filter (e.g., 'ishowspeed', 'mrbeast')
        status: Optional status filter ('pending', 'downloaded', 'uploaded', 'failed')
        limit: Maximum number of videos to return (default: 100)

    Returns:
        List of video dictionaries with link, theme, status, and created_at fields
    """
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT link, theme, COALESCE(status, 'pending') as status, created_at
                FROM videos
            '''
            params = []

            conditions = []
            if theme:
                conditions.append("theme = ?")
                params.append(theme)
            if status:
                conditions.append("COALESCE(status, 'pending') = ?")
                params.append(status)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            videos = []
            for row in cursor.fetchall():
                videos.append({
                    'link': row[0],
                    'theme': row[1],
                    'status': row[2],
                    'created_at': row[3]
                })
            return videos
    except Exception as e:
        logger.error(f"Error getting videos: {e}")
        return []


def count_records(table: str, conditions: Optional[Dict[str, Any]] = None) -> int:
    """Count records in a database table with optional WHERE conditions.

    Args:
        table: Database table name ('accounts', 'videos', 'publicationhistory', etc.)
        conditions: Optional dictionary of column=value conditions for WHERE clause

    Returns:
        Number of matching records, or 0 on error

    Example:
        count_records('accounts', {'active': 1})  # Count active accounts
        count_records('videos')  # Count all videos
    """
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            query = f"SELECT COUNT(*) FROM {table}"
            params = []

            if conditions:
                where_clauses = []
                for key, value in conditions.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)

                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)

            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error counting records in {table}: {e}")
        return 0


def get_table_stats() -> Dict[str, Any]:
    """Get comprehensive statistics for all main database tables.

    Returns detailed counts and breakdowns for accounts, videos, publications,
    TikTok sources, and task logs with status distributions.

    Returns:
        Dictionary containing statistics for all tables with breakdowns by status/type
    """
    try:
        stats = {
            'accounts': {
                'total': count_records('accounts'),
                'active': count_records('accounts', {'active': 1}),
                'with_proxy': count_records('accounts', {'proxy_active': 1})
            },
            'videos': {
                'total': count_records('videos'),
                'by_status': {}
            },
            'publication_history': count_records('publicationhistory'),
            'tiktok_sources': count_records('tiktok_sources'),
            'task_logs': count_records('task_logs')
        }

        # Get video status breakdown
        try:
            with get_database_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT COALESCE(status, 'pending') as status, COUNT(*) as count
                    FROM videos
                    GROUP BY COALESCE(status, 'pending')
                ''')
                for row in cursor.fetchall():
                    stats['videos']['by_status'][row[0]] = row[1]
        except Exception as e:
            logger.error(f"Error getting video status stats: {e}")

        return stats
    except Exception as e:
        logger.error(f"Error getting table stats: {e}")
        return {}