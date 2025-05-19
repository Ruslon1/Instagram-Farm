import psycopg2

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

    cursor.execute("SELECT * FROM Accounts")
    accounts = cursor.fetchall()

    cursor.execute("SELECT * FROM Videos")
    videos = cursor.fetchall()

    cursor.close()
    connection.close()

    return accounts, videos
