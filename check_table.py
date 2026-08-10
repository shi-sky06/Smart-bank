## shows the columns,datatypes in the table###
import sqlite3

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(users)")

columns = cursor.fetchall()

print("---- Users Table Structure ----")

for column in columns:
    print(column)

conn.close()