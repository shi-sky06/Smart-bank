## used to check the userinfo##
import sqlite3

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

# Show usernames and passwords
cursor.execute("SELECT username, password FROM users")

users = cursor.fetchall()

print("---- Registered Users ----")

for user in users:
    print("Username:", user[0])
    print("Password:", user[1])
    print("-------------------------")

conn.close()