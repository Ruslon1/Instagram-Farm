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

    cursor.execute("SELECT username, password, theme FROM Accounts")
    accounts = cursor.fetchall()

    cursor.execute("SELECT link, theme FROM Videos")
    videos = cursor.fetchall()

    account_to_videos = {}
    for link, theme in videos:
        if theme not in account_to_videos:
            account_to_videos[theme] = []
        account_to_videos[theme].append(link)

    cursor.close()
    connection.close()

    return accounts, account_to_videos
