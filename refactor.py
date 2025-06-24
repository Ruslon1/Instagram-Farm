#!/usr/bin/env python3
"""
Script to recreate Instagram Bot database from scratch
"""

import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path

DB_PATH = "instagram_bot.db"
BACKUP_DIR = "database_backups"


def backup_existing_database():
    """Create backup of existing database"""
    if not os.path.exists(DB_PATH):
        print("ℹ️ No existing database to backup")
        return None

    # Create backup directory
    Path(BACKUP_DIR).mkdir(exist_ok=True)

    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{BACKUP_DIR}/instagram_bot_backup_{timestamp}.db"

    try:
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ Failed to backup database: {e}")
        return None


def remove_old_database():
    """Remove old database file"""
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print(f"🗑️ Removed old database: {DB_PATH}")
        except Exception as e:
            print(f"❌ Failed to remove old database: {e}")
            return False
    return True


def create_fresh_database():
    """Create a fresh database with all tables"""
    print("🔨 Creating fresh database...")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Create accounts table
        print("📋 Creating accounts table...")
        cursor.execute('''
                       CREATE TABLE accounts
                       (
                           username         TEXT PRIMARY KEY,
                           password         TEXT NOT NULL,
                           theme            TEXT NOT NULL,
                           "2FAKey"         TEXT,
                           status           TEXT    DEFAULT 'active',
                           active           BOOLEAN DEFAULT TRUE,
                           last_login       TIMESTAMP,
                           posts_count      INTEGER DEFAULT 0,
                           proxy_host       TEXT,
                           proxy_port       INTEGER,
                           proxy_username   TEXT,
                           proxy_password   TEXT,
                           proxy_type       TEXT    DEFAULT 'HTTP',
                           proxy_active     BOOLEAN DEFAULT FALSE,
                           proxy_last_check TIMESTAMP,
                           proxy_status     TEXT    DEFAULT 'unchecked'
                       )
                       ''')

        # Create videos table
        print("📹 Creating videos table...")
        cursor.execute('''
                       CREATE TABLE videos
                       (
                           link       TEXT NOT NULL,
                           theme      TEXT NOT NULL,
                           status     TEXT      DEFAULT 'pending',
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           PRIMARY KEY (link, theme)
                       )
                       ''')

        # Create publication history table
        print("📝 Creating publication history table...")
        cursor.execute('''
                       CREATE TABLE publicationhistory
                       (
                           account_username TEXT NOT NULL,
                           video_link       TEXT NOT NULL,
                           created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
                           PRIMARY KEY (account_username, video_link)
                       )
                       ''')

        # Create TikTok sources table
        print("🎯 Creating tiktok_sources table...")
        cursor.execute('''
                       CREATE TABLE tiktok_sources
                       (
                           id              INTEGER PRIMARY KEY AUTOINCREMENT,
                           theme           TEXT NOT NULL,
                           tiktok_username TEXT NOT NULL,
                           active          BOOLEAN   DEFAULT TRUE,
                           last_fetch      TIMESTAMP,
                           videos_count    INTEGER   DEFAULT 0,
                           created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           UNIQUE (theme, tiktok_username)
                       )
                       ''')

        # Create task logs table
        print("📊 Creating task_logs table...")
        cursor.execute('''
                       CREATE TABLE task_logs
                       (
                           id               TEXT PRIMARY KEY,
                           task_type        TEXT NOT NULL,
                           status           TEXT NOT NULL,
                           account_username TEXT,
                           message          TEXT,
                           progress         INTEGER   DEFAULT 0,
                           total_items      INTEGER   DEFAULT 0,
                           current_item     TEXT,
                           next_action_at   TIMESTAMP,
                           cooldown_seconds INTEGER,
                           created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                       )
                       ''')

        # Create proxy health logs table
        print("🏥 Creating proxy_health_logs table...")
        cursor.execute('''
                       CREATE TABLE proxy_health_logs
                       (
                           id              INTEGER PRIMARY KEY AUTOINCREMENT,
                           check_time      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           total_proxies   INTEGER,
                           working_proxies INTEGER,
                           failed_proxies  INTEGER,
                           results         TEXT
                       )
                       ''')

        # Create indexes
        print("🔍 Creating indexes...")

        # Videos indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_theme ON videos(theme)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at)')

        # Publication history indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_publications_username ON publicationhistory(account_username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_publications_created_at ON publicationhistory(created_at)')

        # TikTok sources indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tiktok_sources_theme ON tiktok_sources(theme)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tiktok_sources_active ON tiktok_sources(active)')

        # Task logs indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_status ON task_logs(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_created_at ON task_logs(created_at)')

        # Accounts proxy indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_proxy_active ON accounts(proxy_active)')

        # Commit all changes
        conn.commit()
        conn.close()

        print("✅ Fresh database created successfully!")

        # Set proper permissions
        os.chmod(DB_PATH, 0o666)
        print("✅ Database permissions set")

        return True

    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False


def add_sample_data():
    """Add some sample data for testing"""
    print("🌱 Adding sample data...")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Add sample TikTok sources
        sample_sources = [
            ("ishowspeed", "ishowdailyupdate3", True),
            ("ishowspeed", "speedyupdates", True),
            ("gaming", "gamingclips", True),
            ("funny", "funnymoments", True),
        ]

        for theme, username, active in sample_sources:
            cursor.execute('''
                           INSERT
                           OR IGNORE INTO tiktok_sources (theme, tiktok_username, active)
                VALUES (?, ?, ?)
                           ''', (theme, username, active))

        conn.commit()
        conn.close()

        print("✅ Sample data added")
        return True

    except Exception as e:
        print(f"❌ Failed to add sample data: {e}")
        return False


def verify_database():
    """Verify the database was created correctly"""
    print("🔍 Verifying database...")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            'accounts',
            'videos',
            'publicationhistory',
            'tiktok_sources',
            'task_logs',
            'proxy_health_logs'
        ]

        print(f"📋 Found tables: {tables}")

        # Check all expected tables exist
        for table in expected_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✅ {table}: {count} rows")
            else:
                print(f"  ❌ {table}: MISSING")
                return False

        # Test database integrity
        cursor.execute("PRAGMA integrity_check")
        integrity = cursor.fetchone()[0]

        if integrity == "ok":
            print("✅ Database integrity check passed")
        else:
            print(f"❌ Database integrity issues: {integrity}")
            return False

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False


def main():
    """Main function to recreate database"""
    print("🔄 Instagram Bot Database Recreation Tool")
    print("=" * 50)

    # Ask for confirmation
    response = input("⚠️  This will DELETE your current database. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ Operation cancelled")
        return

    print("\n🚀 Starting database recreation...")

    # Step 1: Backup existing database
    backup_path = backup_existing_database()

    # Step 2: Remove old database
    if not remove_old_database():
        print("❌ Failed to remove old database")
        return

    # Step 3: Create fresh database
    if not create_fresh_database():
        print("❌ Failed to create fresh database")
        return

    # Step 4: Add sample data
    add_sample_data()

    # Step 5: Verify database
    if not verify_database():
        print("❌ Database verification failed")
        return

    print("\n🎉 Database recreation completed successfully!")
    print(f"📂 Database location: {os.path.abspath(DB_PATH)}")
    if backup_path:
        print(f"💾 Backup saved to: {os.path.abspath(backup_path)}")

    print("\n📋 Next steps:")
    print("1. Add your Instagram accounts via the web interface")
    print("2. Add TikTok sources for your themes")
    print("3. Start fetching and uploading videos")
    print("\n🚀 Run: python3 main.py")


if __name__ == "__main__":
    main()