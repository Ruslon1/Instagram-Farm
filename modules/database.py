import sqlite3
import os
from contextlib import contextmanager

DB_PATH = "instagram_bot.db"


@contextmanager
def get_database_connection():
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()


def init_database():
    """Initialize SQLite database with required tables"""
    with get_database_connection() as connection:
        cursor = connection.cursor()
        cursor.executescript('''
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
                                 TEXT
                             );

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
                                 PRIMARY
                                 KEY
                             (
                                 link,
                                 theme
                             )
                                 );

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
                                 DATETIME
                                 DEFAULT
                                 CURRENT_TIMESTAMP,
                                 PRIMARY
                                 KEY
                             (
                                 account_username,
                                 video_link
                             )
                                 );

                             CREATE INDEX IF NOT EXISTS idx_videos_theme ON videos(theme);
                             CREATE INDEX IF NOT EXISTS idx_publications_username ON publicationhistory(account_username);
                             ''')
        connection.commit()


def load_accounts_and_videos():
    with get_database_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("SELECT username, password, theme, \"2FAKey\" FROM accounts")
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
    with get_database_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO publicationhistory (account_username, video_link) VALUES (?, ?)",
            (username, video_link)
        )
        connection.commit()


def record_video(video_link, theme):
    with get_database_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO videos (link, theme) VALUES (?, ?)",
            (video_link, theme)
        )
        connection.commit()


def get_existing_video_links_for_theme(theme):
    with get_database_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT link FROM videos WHERE theme = ?", (theme,))
        links = {row[0] for row in cursor.fetchall()}
        return links


def is_video_published(username, video_link):
    with get_database_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT 1 FROM publicationhistory "
            "WHERE account_username = ? AND video_link = ?",
            (username, video_link)
        )
        exists = bool(cursor.fetchone())
        return exists