#!/usr/bin/env python3
"""
Migration script to add tiktok_sources table and update task_logs
"""

from modules.database import get_database_connection


def migrate_database():
    """Add tiktok_sources table and update task_logs structure"""

    with get_database_connection() as conn:
        cursor = conn.cursor()

        print("📊 Adding tiktok_sources table...")

        # Create tiktok_sources table
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS tiktok_sources
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           theme
                           TEXT
                           NOT
                           NULL,
                           tiktok_username
                           TEXT
                           NOT
                           NULL,
                           active
                           BOOLEAN
                           DEFAULT
                           TRUE,
                           last_fetch
                           TIMESTAMP,
                           videos_count
                           INTEGER
                           DEFAULT
                           0,
                           created_at
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP,
                           UNIQUE
                       (
                           theme,
                           tiktok_username
                       )
                           )
                       ''')

        # Update task_logs table with progress fields
        print("📊 Updating task_logs table...")

        # Check current columns
        cursor.execute("PRAGMA table_info(task_logs)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add new columns if they don't exist
        new_columns = [
            ("progress", "INTEGER DEFAULT 0"),
            ("total_items", "INTEGER DEFAULT 0"),
            ("current_item", "TEXT"),
            ("next_action_at", "TIMESTAMP"),
            ("cooldown_seconds", "INTEGER")
        ]

        for column_name, column_def in new_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE task_logs ADD COLUMN {column_name} {column_def}")
                    print(f"  ✅ Added column: {column_name}")
                except Exception as e:
                    print(f"  ❌ Failed to add {column_name}: {e}")

        # Create indexes
        cursor.execute('''
                       CREATE INDEX IF NOT EXISTS idx_tiktok_sources_theme
                           ON tiktok_sources(theme)
                       ''')

        cursor.execute('''
                       CREATE INDEX IF NOT EXISTS idx_tiktok_sources_active
                           ON tiktok_sources(active)
                       ''')

        # Insert some default sources if table is empty
        cursor.execute("SELECT COUNT(*) FROM tiktok_sources")
        count = cursor.fetchone()[0]

        if count == 0:
            print("📝 Adding default TikTok sources...")

            default_sources = [
                ("ishowspeed", "ishowdailyupdate3", True),
                ("ishowspeed", "speedyupdates", True),
                ("ishowspeed", "ishowspeedclips", True),
                ("gaming", "gamingclips", True),
                ("funny", "funnymoments", True),
                ("funny", "viralvideos", True),
            ]

            for theme, username, active in default_sources:
                cursor.execute('''
                               INSERT
                               OR IGNORE INTO tiktok_sources (theme, tiktok_username, active)
                    VALUES (?, ?, ?)
                               ''', (theme, username, active))
                print(f"  ➕ Added {username} for theme '{theme}'")

        conn.commit()
        print("✅ Migration completed successfully!")


if __name__ == "__main__":
    migrate_database()