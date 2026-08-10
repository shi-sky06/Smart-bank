import sqlite3

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

cursor.execute("UPDATE users SET password=? WHERE username=?", ("1234", "sky"))
cursor.execute("UPDATE admins SET password=? WHERE username=?", ("admin123", "admin"))

conn.commit()
conn.close()

print("Done.")