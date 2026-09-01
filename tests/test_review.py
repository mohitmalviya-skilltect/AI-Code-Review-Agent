import sqlite3

def fetch_user(connection, username):
    cursor = connection.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}'"
    cursor.execute(query)
    return cursor.fetchall()

def get_user(username):
    connection = sqlite3.connect("users.db")
    return fetch_user(connection, username)
