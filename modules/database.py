import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from urllib.parse import urlparse
from config.settings import settings
from core.logging import get_logger

logger = get_logger("database")


@contextmanager
def get_database_connection():
    """Get database connection context manager."""
    conn = None
    try:
        if settings.database_url.startswith('postgresql'):
            # PostgreSQL connection
            url = urlparse(settings.database_url)
            conn = psycopg2.connect(
                host=url.hostname,
                port=url.port or 5432,
                user=url.username,
                password=url.password,
                database=url.path[1:],  # Remove leading /
                cursor_factory=psycopg2.extras.RealDictCursor
            )
        else:
            # SQLite fallback for development
            import sqlite3
            conn = sqlite3.connect(settings.database_url.replace('sqlite:///', ''))
            conn.row_factory = sqlite3.Row

        yield conn
    except Exception as e:
        logger.error("Database connection error", error=str(e))
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def init_database():
    """Initialize database with all required tables."""
    logger.info("Initializing database")

    is_postgresql = settings.database_url.startswith('postgresql')

    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            if is_postgresql:
                # PostgreSQL schema

                # Create accounts table
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS accounts
                               (
                                   username
                                   VARCHAR
                               (
                                   255
                               ) PRIMARY KEY,
                                   password VARCHAR
                               (
                                   255
                               ) NOT NULL,
                                   theme VARCHAR
                               (
                                   255
                               ) NOT NULL,
                                   "2FAKey" VARCHAR
                               (
                                   255
                               ),
                                   status VARCHAR
                               (
                                   50
                               ) DEFAULT 'active',
                                   active BOOLEAN DEFAULT TRUE,
                                   last_login TIMESTAMP,
                                   posts_count INTEGER DEFAULT 0,
                                   proxy_host VARCHAR
                               (
                                   255
                               ),
                                   proxy_port INTEGER,
                                   proxy_username VARCHAR
                               (
                                   255
                               ),
                                   proxy_password VARCHAR
                               (
                                   255
                               ),
                                   proxy_type VARCHAR
                               (
                                   50
                               ) DEFAULT 'HTTP',
                                   proxy_active BOOLEAN DEFAULT FALSE,
                                   proxy_last_check TIMESTAMP,
                                   proxy_status VARCHAR
                               (
                                   50
                               ) DEFAULT 'unchecked'
                                   )
                               ''')

                # Create videos table
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS videos
                               (
                                   link
                                   VARCHAR
                               (
                                   1000
                               ) NOT NULL,
                                   theme VARCHAR
                               (
                                   255
                               ) NOT NULL,
                                   status VARCHAR
                               (
                                   50
                               ) DEFAULT 'pending',
                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                   PRIMARY KEY
                               (
                                   link,
                                   theme
                               )
                                   )
                               ''')

                # Create publication history table
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS publicationhistory
                               (
                                   account_username
                                   VARCHAR
                               (
                                   255
                               ) NOT NULL,
                                   video_link VARCHAR
                               (
                                   1000
                               ) NOT NULL,
                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                   PRIMARY KEY
                               (
                                   account_username,
                                   video_link
                               )
                                   )
                               ''')

                # Create TikTok sources table
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS tiktok_sources
                               (
                                   id
                                   SERIAL
                                   PRIMARY
                                   KEY,
                                   theme
                                   VARCHAR
                               (
                                   255
                               ) NOT NULL,
                                   tiktok_username VARCHAR
                               (
                                   255
                               ) NOT NULL,
                                   active BOOLEAN DEFAULT TRUE,
                                   last_fetch TIMESTAMP,
                                   videos_count INTEGER DEFAULT 0,
                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                   UNIQUE
                               (
                                   theme,
                                   tiktok_username
                               )
                                   )
                               ''')

                # Create task logs table
                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS task_logs
                               (
                                   id
                                   VARCHAR
                               (
                                   255
                               ) PRIMARY KEY,
                                   task_type VARCHAR
                               (
                                   100
                               ) NOT NULL,
                                   status VARCHAR
                               (
                                   50
                               ) NOT NULL,
                                   account_username VARCHAR
                               (
                                   255
                               ),
                                   message TEXT,
                                   progress INTEGER DEFAULT 0,
                                   total_items INTEGER DEFAULT 0,
                                   current_item TEXT,
                                   next_action_at TIMESTAMP,
                                   cooldown_seconds INTEGER,
                                   created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                                   )
                               ''')

                # Create indexes for performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_theme ON videos(theme)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at)')
                cursor.execute(
                    'CREATE INDEX IF NOT EXISTS idx_publications_username ON publicationhistory(account_username)')
                cursor.execute(
                    'CREATE INDEX IF NOT EXISTS idx_publications_created_at ON publicationhistory(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tiktok_sources_theme ON tiktok_sources(theme)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_tiktok_sources_active ON tiktok_sources(active)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_status ON task_logs(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_created_at ON task_logs(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_proxy_active ON accounts(proxy_active)')

            else:
                # SQLite schema (for development)

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS accounts
                               (
                                   username
                                   TEXT
                                   PRIMARY
                                   KEY,
                                   password
                                   TEXT
                                   NOT
                                   NULL,
                                   theme
                                   TEXT
                                   NOT
                                   NULL,
                                   "2FAKey"
                                   TEXT,
                                   status
                                   TEXT
                                   DEFAULT
                                   'active',
                                   active
                                   BOOLEAN
                                   DEFAULT
                                   1,
                                   last_login
                                   TIMESTAMP,
                                   posts_count
                                   INTEGER
                                   DEFAULT
                                   0,
                                   proxy_host
                                   TEXT,
                                   proxy_port
                                   INTEGER,
                                   proxy_username
                                   TEXT,
                                   proxy_password
                                   TEXT,
                                   proxy_type
                                   TEXT
                                   DEFAULT
                                   'HTTP',
                                   proxy_active
                                   BOOLEAN
                                   DEFAULT
                                   0,
                                   proxy_last_check
                                   TIMESTAMP,
                                   proxy_status
                                   TEXT
                                   DEFAULT
                                   'unchecked'
                               )
                               ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS videos
                               (
                                   link
                                   TEXT
                                   NOT
                                   NULL,
                                   theme
                                   TEXT
                                   NOT
                                   NULL,
                                   status
                                   TEXT
                                   DEFAULT
                                   'pending',
                                   created_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP,
                                   PRIMARY
                                   KEY
                               (
                                   link,
                                   theme
                               )
                                   )
                               ''')

                cursor.execute('''
                               CREATE TABLE IF NOT EXISTS publicationhistory
                               (
                                   account_username
                                   TEXT
                                   NOT
                                   NULL,
                                   video_link
                                   TEXT
                                   NOT
                                   NULL,
                                   created_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP,
                                   PRIMARY
                                   KEY
                               (
                                   account_username,
                                   video_link
                               )
                                   )
                               ''')

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
                                   1,
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
                                   progress
                                   INTEGER
                                   DEFAULT
                                   0,
                                   total_items
                                   INTEGER
                                   DEFAULT
                                   0,
                                   current_item
                                   TEXT,
                                   next_action_at
                                   TIMESTAMP,
                                   cooldown_seconds
                                   INTEGER,
                                   created_at
                                   TIMESTAMP
                                   DEFAULT
                                   CURRENT_TIMESTAMP
                               )
                               ''')

            conn.commit()
            logger.info("Database initialized successfully")

    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


# PostgreSQL-compatible functions
def load_accounts_and_videos():
    """Load accounts and videos (compatibility function)."""
    with get_database_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT username, password, theme, "2FAKey" FROM accounts')
        accounts = cursor.fetchall()

        cursor.execute("SELECT link, theme FROM videos")
        all_videos = cursor.fetchall()

        cursor.execute("SELECT account_username, video_link FROM publicationhistory")
        published = cursor.fetchall()
        published_set = set(published)

        account_to_videos = {}
        for link, theme in all_videos:
            if theme not in account_to_videos:
                account_to_videos[theme] = []
            account_to_videos[theme].append(link)

        return accounts, account_to_videos, published_set


def record_publication(username, video_link):
    """Record video publication."""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            if settings.database_url.startswith('postgresql'):
                cursor.execute('''
                               INSERT INTO publicationhistory (account_username, video_link)
                               VALUES (%s, %s) ON CONFLICT DO NOTHING
                               ''', (username, video_link))
            else:
                cursor.execute('''
                               INSERT
                               OR IGNORE INTO publicationhistory (account_username, video_link)
                    VALUES (?, ?)
                               ''', (username, video_link))

            conn.commit()
            logger.info("Publication recorded", username=username, video_link=video_link[:50] + "...")
    except Exception as e:
        logger.error("Failed to record publication", error=str(e))


def record_video(video_link, theme):
    """Record video."""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            if settings.database_url.startswith('postgresql'):
                cursor.execute('''
                               INSERT INTO videos (link, theme)
                               VALUES (%s, %s) ON CONFLICT (link, theme) DO NOTHING
                               ''', (video_link, theme))
            else:
                cursor.execute('''
                               INSERT
                               OR IGNORE INTO videos (link, theme)
                    VALUES (?, ?)
                               ''', (video_link, theme))

            conn.commit()
            logger.info("Video recorded", theme=theme, video_link=video_link[:50] + "...")
    except Exception as e:
        logger.error("Failed to record video", error=str(e))


def get_existing_video_links_for_theme(theme):
    """Get existing video links for theme."""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            if settings.database_url.startswith('postgresql'):
                cursor.execute("SELECT link FROM videos WHERE theme = %s", (theme,))
            else:
                cursor.execute("SELECT link FROM videos WHERE theme = ?", (theme,))

            links = {row[0] for row in cursor.fetchall()}
            return links
    except Exception as e:
        logger.error("Failed to get existing video links", error=str(e))
        return set()


def is_video_published(username, video_link):
    """Check if video was published by user."""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            if settings.database_url.startswith('postgresql'):
                cursor.execute('''
                               SELECT 1
                               FROM publicationhistory
                               WHERE account_username = %s
                                 AND video_link = %s
                               ''', (username, video_link))
            else:
                cursor.execute('''
                               SELECT 1
                               FROM publicationhistory
                               WHERE account_username = ?
                                 AND video_link = ?
                               ''', (username, video_link))

            exists = cursor.fetchone() is not None
            return exists
    except Exception as e:
        logger.error("Failed to check video publication", error=str(e))
        return False