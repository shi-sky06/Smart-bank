##used for adding email in the database#
import sqlite3

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

cursor.execute("""
ALTER TABLE users ADD COLUMN email TEXT
""")

conn.commit()
conn.close()

print("✅ Email column added successfully")