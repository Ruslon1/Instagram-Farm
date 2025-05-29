import psycopg2
import os

def get_database_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )

def load_accounts_and_videos():
    connection = get_database_connection()
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

    cursor.close()
    connection.close()

    return accounts, account_to_videos, published_set

def record_publication(username, video_link):
    connection = get_database_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO publicationhistory (account_username, video_link) VALUES (%s, %s)",
        (username, video_link)
    )
    connection.commit()
    cursor.close()
    connection.close()

def record_video(video_link, theme):
    connection = get_database_connection()
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO videos (link, theme) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (video_link, theme)
    )
    connection.commit()
    cursor.close()
    connection.close()

def get_existing_video_links_for_theme(theme):
    connection = get_database_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT link FROM videos WHERE theme = %s", (theme,))
    links = {row[0] for row in cursor.fetchall()}
    cursor.close()
    connection.close()
    return links

def is_video_published(username, video_link):
    connection = get_database_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT 1 FROM publicationhistory "
        "WHERE account_username = %s AND video_link = %s",
        (username, video_link)
    )
    exists = bool(cursor.fetchone())
    cursor.close()
    connection.close()
    return exists