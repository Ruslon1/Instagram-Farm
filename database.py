import sqlite3

sqlite3.Cursor = None

def init_database():
    return sqlite3.connect("database.sqlite").cursor

