#!/usr/bin/env python3
"""
Fix videos table structure
"""

from modules.database import get_database_connection


def fix_videos_table():
    """Add missing columns to videos table"""

    with get_database_connection() as conn:
        cursor = conn.cursor()

        print("🔧 Fixing videos table structure...")

        # Check current table structure
        cursor.execute("PRAGMA table_info(videos)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Current columns: {columns}")

        # Add missing columns if they don't exist
        missing_columns = [
            ("status", "TEXT DEFAULT 'pending'"),
            ("title", "TEXT"),
            ("author", "TEXT"),
            ("views", "INTEGER DEFAULT 0"),
            ("likes", "INTEGER DEFAULT 0"),
            ("duration", "INTEGER"),
            ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        ]

        for column_name, column_def in missing_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE videos ADD COLUMN {column_name} {column_def}")
                    print(f"  ✅ Added column: {column_name}")
                except Exception as e:
                    print(f"  ❌ Failed to add {column_name}: {e}")

        # Add ID column if it doesn't exist (for better management)
        if "id" not in columns:
            print("🔄 Recreating videos table with ID column...")

            # Create new table with proper structure
            cursor.execute('''
                           CREATE TABLE videos_new
                           (
                               id         INTEGER PRIMARY KEY AUTOINCREMENT,
                               link       TEXT NOT NULL,
                               theme      TEXT NOT NULL,
                               title      TEXT,
                               author     TEXT,
                               views      INTEGER   DEFAULT 0,
                               likes      INTEGER   DEFAULT 0,
                               duration   INTEGER,
                               status     TEXT      DEFAULT 'pending',
                               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               UNIQUE (link, theme)
                           )
                           ''')

            # Copy data from old table
            cursor.execute('''
                           INSERT INTO videos_new (link, theme, status, created_at)
                           SELECT link,
                                  theme,
                                  COALESCE(status, 'pending')             as status,
                                  COALESCE(created_at, CURRENT_TIMESTAMP) as created_at
                           FROM videos
                           ''')

            # Drop old table and rename new one
            cursor.execute("DROP TABLE videos")
            cursor.execute("ALTER TABLE videos_new RENAME TO videos")

            print("  ✅ Recreated videos table with ID column")

        # Create indexes for better performance
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_theme ON videos(theme)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)")
            print("  ✅ Created indexes")
        except Exception as e:
            print(f"  ⚠️ Index creation warning: {e}")

        conn.commit()
        print("✅ Videos table fixed successfully!")

        # Show final structure
        cursor.execute("PRAGMA table_info(videos)")
        final_columns = [(row[1], row[2]) for row in cursor.fetchall()]
        print(f"Final table structure:")
        for col_name, col_type in final_columns:
            print(f"  - {col_name}: {col_type}")


if __name__ == "__main__":
    fix_videos_table()