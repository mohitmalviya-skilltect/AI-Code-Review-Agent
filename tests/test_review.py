import sqlite3

def get_user(username):
    connection = sqlite3.connect("users.db")
    cursor = connection.cursor()

    query = f"SELECT * FROM users WHERE username = '{username}'"

    cursor.execute(query)

    return cursor.fetchall()