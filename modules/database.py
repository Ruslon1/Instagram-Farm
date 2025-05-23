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

    cursor.execute("SELECT username, password, theme FROM accounts")
    accounts = cursor.fetchall()

    cursor.execute("SELECT link, theme FROM videos")
    all_videos = cursor.fetchall()

    # Fetch already published videos
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

    return accounts, account_to_videos

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