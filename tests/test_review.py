import sqlite3

username = input("Username: ")
password = input("Password: ")

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
cursor.execute(query)

print(cursor.fetchall())