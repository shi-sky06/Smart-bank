import sqlite3

conn = sqlite3.connect("bank.db")
result = conn.execute("SELECT username, password FROM users WHERE username='sky'").fetchall()
print(result)
conn.close()