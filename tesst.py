import sqlite3

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")

print("USERS TABLE STRUCTURE:")
for column in cursor.fetchall():
    print(column)

conn.close()