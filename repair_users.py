"""
reset_passwords.py

One-time fix: resets any bcrypt-hashed passwords in bank.db back to
plain text, matching security.py's simplified verify_password.

Usage: python reset_passwords.py
"""

import sqlite3

NEW_PASSWORD = "changeme123"  # set whatever you want everyone's password to become

conn = sqlite3.connect("bank.db")
cursor = conn.cursor()

cursor.execute("SELECT id, username, password FROM users")
users = cursor.fetchall()

hashed_users = [u for u in users if isinstance(u[2], str) and u[2].startswith(("$2a$", "$2b$", "$2y$"))]

if not hashed_users:
    print("No hashed passwords found — nothing to fix.")
else:
    print(f"Found {len(hashed_users)} account(s) with hashed passwords:")
    for user_id, username, _ in hashed_users:
        print(f"  - {username} (id {user_id})")

    confirm = input(f"\nReset all of these to password \"{NEW_PASSWORD}\"? (yes/no): ").strip().lower()

    if confirm == "yes":
        for user_id, username, _ in hashed_users:
            cursor.execute("UPDATE users SET password=? WHERE id=?", (NEW_PASSWORD, user_id))
        conn.commit()
        print(f"\nDone. {len(hashed_users)} account(s) reset. New password: {NEW_PASSWORD}")
    else:
        print("Cancelled — no changes made.")

conn.close()