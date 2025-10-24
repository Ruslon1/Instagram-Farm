"""
Database utility functions to reduce code duplication
"""

from typing import List, Dict, Any, Optional, Tuple
from modules.database import get_database_connection
from core.logging import get_logger

logger = get_logger("database_utils")


def get_account_by_username(username: str) -> Optional[Tuple]:
    """Get account data by username"""
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
    """Check if account exists"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM accounts WHERE username = ?", (username,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking account existence {username}: {e}")
        return False


def video_exists(video_link: str) -> bool:
    """Check if video exists"""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM videos WHERE link = ?", (video_link,))
            return cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking video existence {video_link}: {e}")
        return False


def get_active_accounts() -> List[Dict[str, Any]]:
    """Get all active accounts with their data"""
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
    """Get videos with optional filtering"""
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
    """Count records in a table with optional conditions"""
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
    """Get statistics for all main tables"""
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