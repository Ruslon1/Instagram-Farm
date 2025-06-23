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

                # Create task_logs table if it doesn't exist (with new columns)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS task_logs (
                        id TEXT PRIMARY KEY,
                        task_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        account_username TEXT,
                        message TEXT,
                        progress INTEGER DEFAULT 0,
                        total_items INTEGER DEFAULT 0,
                        current_item TEXT,
                        next_action_at TIMESTAMP,
                        cooldown_seconds INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Calculate next action time if cooldown is provided
                next_action_at = None
                if cooldown_seconds and status == "running":
                    next_action_at = (datetime.now() + timedelta(seconds=cooldown_seconds)).isoformat()

                # Insert or update task log
                cursor.execute('''
                    INSERT OR REPLACE INTO task_logs 
                    (id, task_type, status, account_username, message, progress, total_items, 
                     current_item, next_action_at, cooldown_seconds, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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

            # Ensure all columns exist
            cursor.execute("PRAGMA table_info(task_logs)")
            columns = [row[1] for row in cursor.fetchall()]

            # Build select statement based on available columns
            base_fields = "id, task_type, status, account_username, message, created_at"

            additional_fields = []
            if "progress" in columns:
                additional_fields.append("progress")
            else:
                additional_fields.append("0 as progress")

            if "total_items" in columns:
                additional_fields.append("total_items")
            else:
                additional_fields.append("0 as total_items")

            if "current_item" in columns:
                additional_fields.append("current_item")
            else:
                additional_fields.append("NULL as current_item")

            if "next_action_at" in columns:
                additional_fields.append("next_action_at")
            else:
                additional_fields.append("NULL as next_action_at")

            if "cooldown_seconds" in columns:
                additional_fields.append("cooldown_seconds")
            else:
                additional_fields.append("NULL as cooldown_seconds")

            select_fields = f"{base_fields}, {', '.join(additional_fields)}"

            if status:
                cursor.execute(f'''
                    SELECT {select_fields}
                    FROM task_logs 
                    WHERE status = ?
                    ORDER BY created_at DESC 
                    LIMIT ?
                ''', (status, limit))
            else:
                cursor.execute(f'''
                    SELECT {select_fields}
                    FROM task_logs 
                    ORDER BY created_at DESC 
                    LIMIT ?
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
                    SET progress = ?, current_item = ?, message = ?, 
                        next_action_at = ?, cooldown_seconds = ?, created_at = ?
                    WHERE id = ?
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
                        SET status = ?, message = ?, next_action_at = NULL, 
                            cooldown_seconds = NULL, created_at = ?, 
                            progress = CASE WHEN status = 'running' THEN progress ELSE 100 END
                        WHERE id = ?
                    ''', (status, message, datetime.now().isoformat(), task_id))
                else:
                    cursor.execute('''
                        UPDATE task_logs 
                        SET status = ?, message = ?, created_at = ?
                        WHERE id = ?
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
                           COALESCE(progress, 0) as progress,
                           COALESCE(total_items, 0) as total_items,
                           current_item, next_action_at, cooldown_seconds
                    FROM task_logs 
                    WHERE id = ?
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