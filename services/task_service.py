from typing import List, Optional
from datetime import datetime
from modules.database import get_database_connection
from api.models import TaskLog


class TaskService:
    """Service for managing task logs and operations"""

    @staticmethod
    async def log_task(task_id: str, task_type: str, status: str,
                       account_username: Optional[str] = None,
                       message: Optional[str] = None):
        """Log task status to database"""
        try:
            with get_database_connection() as conn:
                cursor = conn.cursor()

                # Create task_logs table if it doesn't exist
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS task_logs
                               (
                                   id
                                   TEXT
                                   PRIMARY
                                   KEY,
                                   task_type
                                   TEXT
                                   NOT
                                   NULL,
                                   status
                                   TEXT
                                   NOT
                                   NULL,
                                   account_username
                                   TEXT,
                                   message
                                   TEXT,
                                   created_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP
                               )
                               ''')

                # Insert or update task log
                cursor.execute('''
                    INSERT OR REPLACE INTO task_logs 
                    (id, task_type, status, account_username, message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (task_id, task_type, status, account_username, message, datetime.now().isoformat()))

                conn.commit()

        except Exception as e:
            print(f"Failed to log task: {e}")

    @staticmethod
    async def get_recent_tasks(status: Optional[str] = None, limit: int = 50) -> List[TaskLog]:
        """Get recent task logs"""
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Create table if it doesn't exist
            cursor.execute('''
                           CREATE TABLE IF NOT EXISTS task_logs
                           (
                               id
                               TEXT
                               PRIMARY
                               KEY,
                               task_type
                               TEXT
                               NOT
                               NULL,
                               status
                               TEXT
                               NOT
                               NULL,
                               account_username
                               TEXT,
                               message
                               TEXT,
                               created_at
                               TIMESTAMP
                               DEFAULT
                               CURRENT_TIMESTAMP
                           )
                           ''')

            if status:
                cursor.execute('''
                               SELECT id, task_type, status, account_username, message, created_at
                               FROM task_logs
                               WHERE status = ?
                               ORDER BY created_at DESC LIMIT ?
                               ''', (status, limit))
            else:
                cursor.execute('''
                               SELECT id, task_type, status, account_username, message, created_at
                               FROM task_logs
                               ORDER BY created_at DESC LIMIT ?
                               ''', (limit,))

            tasks = []
            for row in cursor.fetchall():
                tasks.append(TaskLog(
                    id=row[0],
                    task_type=row[1],
                    status=row[2],
                    account_username=row[3],
                    message=row[4],
                    created_at=row[5] or datetime.now().isoformat()
                ))

            return tasks

    @staticmethod
    async def update_task_status(task_id: str, status: str, message: Optional[str] = None):
        """Update task status"""
        try:
            with get_database_connection() as conn:
                cursor = conn.cursor()

                if message:
                    cursor.execute('''
                                   UPDATE task_logs
                                   SET status     = ?,
                                       message    = ?,
                                       created_at = ?
                                   WHERE id = ?
                                   ''', (status, message, datetime.now().isoformat(), task_id))
                else:
                    cursor.execute('''
                                   UPDATE task_logs
                                   SET status     = ?,
                                       created_at = ?
                                   WHERE id = ?
                                   ''', (status, datetime.now().isoformat(), task_id))

                conn.commit()

        except Exception as e:
            print(f"Failed to update task status: {e}")