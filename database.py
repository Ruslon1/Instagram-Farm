import sqlite3

def init_database():
    db = sqlite3.connect("database.sqlite")
    accounts = db.execute("SELECT * FROM Accounts").fetchall()
    videos = db.execute("SELECT * FROM Videos").fetchall()
    return accounts, videos
