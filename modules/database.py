import sqlite3
from contextlib import contextmanager
from config.settings import settings
from core.logging import get_logger

logger = get_logger("database")


@contextmanager
def get_database_connection():
    """Get SQLite database connection context manager with better error handling."""
    conn = None
    try:
        # SQLite connection
        db_path = settings.database_url.replace('sqlite:///', '')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")
        # Set synchronous mode for better performance/safety balance
        conn.execute("PRAGMA synchronous = NORMAL")

        yield conn
    except Exception as e:
        logger.error("Database connection error", error=str(e))
        if conn:
            try:
                conn.rollback()
            except:
                pass
        raise
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


def safe_fetchone(cursor, default=None):
    """Safely fetch one result with default value."""
    try:
        result = cursor.fetchone()
        if result:
            return result
        return default
    except Exception as e:
        logger.error("Error in fetchone", error=str(e))
        return default


def safe_fetchall(cursor, default=None):
    """Safely fetch all results with default value."""
    try:
        result = cursor.fetchall()
        if result:
            return result
        return default or []
    except Exception as e:
        logger.error("Error in fetchall", error=str(e))
        return default or []


def init_database():
    """Initialize SQLite database with all required tables."""
    logger.info("Initializing SQLite database")

    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # SQLite schema

            # Create accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    username TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    theme TEXT NOT NULL,
                    "2FAKey" TEXT,
                    status TEXT DEFAULT 'active',
                    active BOOLEAN DEFAULT 1,
                    last_login TIMESTAMP,
                    posts_count INTEGER DEFAULT 0,
                    proxy_host TEXT,
                    proxy_port INTEGER,
                    proxy_username TEXT,
                    proxy_password TEXT,
                    proxy_type TEXT DEFAULT 'HTTP',
                    proxy_active BOOLEAN DEFAULT 0,
                    proxy_last_check TIMESTAMP,
                    proxy_status TEXT DEFAULT 'unchecked'
                )
            ''')

            # Create videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    link TEXT NOT NULL,
                    theme TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (link, theme)
                )
            ''')

            # Create publication history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS publicationhistory (
                    account_username TEXT NOT NULL,
                    video_link TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (account_username, video_link)
                )
            ''')

            # Create TikTok sources table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tiktok_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    theme TEXT NOT NULL,
                    tiktok_username TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    last_fetch TIMESTAMP,
                    videos_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (theme, tiktok_username)
                )
            ''')

            # Create task logs table
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

            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_theme ON videos(theme)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_publications_username ON publicationhistory(account_username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_publications_created_at ON publicationhistory(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tiktok_sources_theme ON tiktok_sources(theme)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tiktok_sources_active ON tiktok_sources(active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_status ON task_logs(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_task_logs_created_at ON task_logs(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_proxy_active ON accounts(proxy_active)')

            conn.commit()
            logger.info("SQLite database initialized successfully")

    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


# PostgreSQL-compatible functions with better error handling
def load_accounts_and_videos():
    """Load accounts and videos (compatibility function)."""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # Get accounts with safe fetching
            cursor.execute('SELECT username, password, theme, "2FAKey" FROM accounts')
            accounts = safe_fetchall(cursor, [])

            # Get all videos with safe fetching
            cursor.execute("SELECT link, theme FROM videos")
            all_videos = safe_fetchall(cursor, [])

            # Get published videos with safe fetching
            cursor.execute("SELECT account_username, video_link FROM publicationhistory")
            published = safe_fetchall(cursor, [])
            published_set = set(published) if published else set()

            # Group videos by theme
            account_to_videos = {}
            for video_row in all_videos:
                if len(video_row) >= 2:
                    link, theme = video_row[0], video_row[1]
                    if theme not in account_to_videos:
                        account_to_videos[theme] = []
                    account_to_videos[theme].append(link)

            return accounts, account_to_videos, published_set

    except Exception as e:
        logger.error("Error loading accounts and videos", error=str(e))
        return [], {}, set()


def record_publication(username, video_link):
    """Record video publication with better error handling."""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # SQLite INSERT OR IGNORE (equivalent to ON CONFLICT DO NOTHING)
            cursor.execute('''
                INSERT OR IGNORE INTO publicationhistory (account_username, video_link)
                VALUES (?, ?)
            ''', (username, video_link))

            conn.commit()
            logger.info("Publication recorded", username=username, video_link=video_link[:50] + "...")
    except Exception as e:
        logger.error("Failed to record publication", error=str(e))


def record_video(video_link, theme):
    """Record video with better error handling."""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            # SQLite INSERT OR IGNORE (equivalent to ON CONFLICT DO NOTHING)
            cursor.execute('''
                INSERT OR IGNORE INTO videos (link, theme)
                VALUES (?, ?)
            ''', (video_link, theme))

            conn.commit()
            logger.info("Video recorded", theme=theme, video_link=video_link[:50] + "...")
    except Exception as e:
        logger.error("Failed to record video", error=str(e))


def get_existing_video_links_for_theme(theme):
    """Get existing video links for theme with better error handling."""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT link FROM videos WHERE theme = ?", (theme,))

            results = safe_fetchall(cursor, [])
            links = {row[0] for row in results if row and len(row) > 0}
            return links
    except Exception as e:
        logger.error("Failed to get existing video links", error=str(e))
        return set()


def is_video_published(username, video_link):
    """Check if video was published by user with better error handling."""
    try:
        with get_database_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT 1
                FROM publicationhistory
                WHERE account_username = ?
                  AND video_link = ?
            ''', (username, video_link))

            result = safe_fetchone(cursor)
            exists = result is not None
            return exists
    except Exception as e:
        logger.error("Failed to check video publication", error=str(e))
        return False