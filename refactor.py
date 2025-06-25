#!/usr/bin/env python3
"""
Quick PostgreSQL setup script for Instagram Bot
"""

import os
import sys
from urllib.parse import urlparse


def check_postgresql_connection():
    """Check if we can connect to PostgreSQL."""
    try:
        import psycopg2
        from config.settings import settings

        url = urlparse(settings.database_url)

        print(f"🔗 Connecting to PostgreSQL: {url.hostname}:{url.port or 5432}/{url.path[1:]}")

        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port or 5432,
            user=url.username,
            password=url.password,
            database=url.path[1:]
        )

        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]

        print(f"✅ PostgreSQL connection successful!")
        print(f"📋 Version: {version}")

        conn.close()
        return True

    except ImportError:
        print("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\n💡 Make sure:")
        print("1. PostgreSQL is running")
        print("2. Database exists")
        print("3. User has permissions")
        print("4. DATABASE_URL in .env is correct")
        return False


def create_database_if_not_exists():
    """Create database if it doesn't exist."""
    try:
        import psycopg2
        from config.settings import settings

        url = urlparse(settings.database_url)
        db_name = url.path[1:]

        # Connect to postgres database to create our database
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port or 5432,
            user=url.username,
            password=url.password,
            database='postgres'  # Connect to default database
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()

        if not exists:
            print(f"🗄️ Creating database: {db_name}")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Database {db_name} created successfully!")
        else:
            print(f"✅ Database {db_name} already exists")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False


def initialize_tables():
    """Initialize database tables."""
    try:
        from modules.database import init_database

        print("🔨 Initializing database tables...")
        init_database()
        print("✅ Database tables initialized successfully!")
        return True

    except Exception as e:
        print(f"❌ Failed to initialize tables: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 Instagram Bot PostgreSQL Setup")
    print("=" * 50)

    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("📋 Please create .env file with DATABASE_URL")
        print("📝 Example: DATABASE_URL=postgresql://user:pass@localhost:5432/instagram_bot")
        return False

    # Load settings
    try:
        from config.settings import settings

        if not settings.database_url.startswith('postgresql'):
            print("⚠️  DATABASE_URL is not PostgreSQL")
            print(f"📋 Current: {settings.database_url}")
            print("📝 Expected: postgresql://user:pass@host:port/database")

            # Allow SQLite for development
            if settings.database_url.startswith('sqlite'):
                print("🔄 SQLite detected - using existing database module")
                return True
            else:
                return False

    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return False

    # Step 1: Check connection
    print("\n📡 Step 1: Checking PostgreSQL connection...")
    if not check_postgresql_connection():
        # Try to create database
        print("\n🔨 Step 2: Attempting to create database...")
        if not create_database_if_not_exists():
            return False

        # Try connection again
        if not check_postgresql_connection():
            return False

    # Step 2: Initialize tables
    print("\n🏗️ Step 3: Initializing database tables...")
    if not initialize_tables():
        return False

    print("\n🎉 PostgreSQL setup completed successfully!")
    print("🚀 You can now run: python main.py")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)