from typing import List, Optional
from datetime import datetime, timedelta
from modules.database import get_database_connection
from api.models import TaskLog

class TaskService:
    """Service for managing task logs and operations"""

    @staticmethod
    async def log_task(task_id: str, task_type: str, status: str,
                      account_username: Optional[str] = None,
                      message: Optional[str] = None,
                      progress: Optional[int] = None,
                      total_items: Optional[int] = None,
                      current_item: Optional[str] = None,
                      cooldown_seconds: Optional[int] = None):
        """Log task status to database with detailed progress"""
        try:
            with get_database_connection() as conn:
                cursor = conn.cursor()

                # Calculate next action time if cooldown is provided
                next_action_at = None
                if cooldown_seconds and status == "running":
                    next_action_at = (datetime.now() + timedelta(seconds=cooldown_seconds)).isoformat()

                # Insert or update task log (PostgreSQL compatible)
                cursor.execute('''
                    INSERT INTO task_logs 
                    (id, task_type, status, account_username, message, progress, total_items, 
                     current_item, next_action_at, cooldown_seconds, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        task_type = EXCLUDED.task_type,
                        status = EXCLUDED.status,
                        account_username = EXCLUDED.account_username,
                        message = EXCLUDED.message,
                        progress = EXCLUDED.progress,
                        total_items = EXCLUDED.total_items,
                        current_item = EXCLUDED.current_item,
                        next_action_at = EXCLUDED.next_action_at,
                        cooldown_seconds = EXCLUDED.cooldown_seconds,
                        created_at = EXCLUDED.created_at
                ''', (task_id, task_type, status, account_username, message,
                      progress or 0, total_items or 0, current_item, next_action_at,
                      cooldown_seconds, datetime.now().isoformat()))

                conn.commit()

        except Exception as e:
            print(f"Failed to log task: {e}")

    @staticmethod
    async def get_recent_tasks(status: Optional[str] = None, limit: int = 50) -> List[TaskLog]:
        """Get recent task logs with progress information"""
        with get_database_connection() as conn:
            cursor = conn.cursor()

            if status:
                cursor.execute('''
                    SELECT id, task_type, status, account_username, message, created_at,
                           progress, total_items, current_item, next_action_at, cooldown_seconds
                    FROM task_logs 
                    WHERE status = %s
                    ORDER BY created_at DESC 
                    LIMIT %s
                ''', (status, limit))
            else:
                cursor.execute('''
                    SELECT id, task_type, status, account_username, message, created_at,
                           progress, total_items, current_item, next_action_at, cooldown_seconds
                    FROM task_logs 
                    ORDER BY created_at DESC 
                    LIMIT %s
                ''', (limit,))

            tasks = []
            for row in cursor.fetchall():
                tasks.append(TaskLog(
                    id=row[0],
                    task_type=row[1],
                    status=row[2],
                    account_username=row[3],
                    message=row[4],
                    created_at=row[5] or datetime.now().isoformat(),
                    progress=row[6] if len(row) > 6 else 0,
                    total_items=row[7] if len(row) > 7 else 0,
                    current_item=row[8] if len(row) > 8 else None,
                    next_action_at=row[9] if len(row) > 9 else None,
                    cooldown_seconds=row[10] if len(row) > 10 else None
                ))

            return tasks

    @staticmethod
    async def update_task_progress(task_id: str, progress: int, current_item: str,
                                 message: Optional[str] = None, cooldown_seconds: Optional[int] = None):
        """Update task progress with current item and cooldown info"""
        try:
            with get_database_connection() as conn:
                cursor = conn.cursor()

                # Calculate next action time if cooldown is provided
                next_action_at = None
                if cooldown_seconds:
                    next_action_at = (datetime.now() + timedelta(seconds=cooldown_seconds)).isoformat()

                cursor.execute('''
                    UPDATE task_logs 
                    SET progress = %s, 
                        current_item = %s, 
                        message = %s, 
                        next_action_at = %s, 
                        cooldown_seconds = %s, 
                        created_at = %s
                    WHERE id = %s
                ''', (progress, current_item, message, next_action_at,
                      cooldown_seconds, datetime.now().isoformat(), task_id))

                conn.commit()

        except Exception as e:
            print(f"Failed to update task progress: {e}")

    @staticmethod
    async def update_task_status(task_id: str, status: str, message: Optional[str] = None):
        """Update task status"""
        try:
            with get_database_connection() as conn:
                cursor = conn.cursor()

                # Clear next_action_at and cooldown when task completes or is cancelled
                if status in ["success", "failed", "cancelled"]:
                    cursor.execute('''
                        UPDATE task_logs 
                        SET status = %s, 
                            message = %s, 
                            next_action_at = NULL, 
                            cooldown_seconds = NULL, 
                            created_at = %s, 
                            progress = CASE WHEN status = 'running' THEN progress ELSE 100 END
                        WHERE id = %s
                    ''', (status, message, datetime.now().isoformat(), task_id))
                else:
                    cursor.execute('''
                        UPDATE task_logs 
                        SET status = %s, 
                            message = %s, 
                            created_at = %s
                        WHERE id = %s
                    ''', (status, message, datetime.now().isoformat(), task_id))

                conn.commit()

                # Log the status change
                print(f"Task {task_id} status updated to: {status}")

        except Exception as e:
            print(f"Failed to update task status: {e}")

    @staticmethod
    async def get_task_progress(task_id: str) -> Optional[TaskLog]:
        """Get current progress for a specific task"""
        try:
            with get_database_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT id, task_type, status, account_username, message, created_at,
                           CASE WHEN progress IS NULL THEN 0 ELSE progress END as progress,
                           CASE WHEN total_items IS NULL THEN 0 ELSE total_items END as total_items,
                           current_item, next_action_at, cooldown_seconds
                    FROM task_logs 
                    WHERE id = %s
                ''', (task_id,))

                row = cursor.fetchone()
                if row:
                    return TaskLog(
                        id=row[0],
                        task_type=row[1],
                        status=row[2],
                        account_username=row[3],
                        message=row[4],
                        created_at=row[5],
                        progress=row[6],
                        total_items=row[7],
                        current_item=row[8],
                        next_action_at=row[9],
                        cooldown_seconds=row[10]
                    )

                return None

        except Exception as e:
            print(f"Failed to get task progress: {e}")
            return None