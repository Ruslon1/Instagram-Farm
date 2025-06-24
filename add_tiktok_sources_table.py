#!/usr/bin/env python3
"""
Migration script to add proxy support to accounts table
"""

from modules.database import get_database_connection


def migrate_proxy_support():
    """Add proxy columns to accounts table"""

    with get_database_connection() as conn:
        cursor = conn.cursor()

        print("📡 Adding proxy support to accounts table...")

        # Check current columns
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [row[1] for row in cursor.fetchall()]

        # Add proxy columns if they don't exist
        proxy_columns = [
            ("proxy_host", "TEXT"),
            ("proxy_port", "INTEGER"),
            ("proxy_username", "TEXT"),
            ("proxy_password", "TEXT"),
            ("proxy_type", "TEXT DEFAULT 'HTTP'"),
            ("proxy_active", "BOOLEAN DEFAULT FALSE"),
            ("proxy_last_check", "TIMESTAMP"),
            ("proxy_status", "TEXT DEFAULT 'unchecked'")
        ]

        for column_name, column_def in proxy_columns:
            if column_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE accounts ADD COLUMN {column_name} {column_def}")
                    print(f"  ✅ Added column: {column_name}")
                except Exception as e:
                    print(f"  ❌ Failed to add {column_name}: {e}")

        # Create index for proxy lookups
        cursor.execute('''
                       CREATE INDEX IF NOT EXISTS idx_accounts_proxy_active
                           ON accounts(proxy_active)
                       ''')

        conn.commit()
        print("✅ Proxy migration completed successfully!")


if __name__ == "__main__":
    migrate_proxy_support()