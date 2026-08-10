import sqlite3


def create_database():
    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    # =========================
    # Users Table
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        balance REAL DEFAULT 0
    )
    """)

    # =========================
    # Transactions Table
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        transaction_type TEXT,
        receiver TEXT,
        amount REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    # =========================
    # Loans Table
    # =========================
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        loan_type TEXT,
        amount REAL,
        duration INTEGER,
        interest REAL,
        status TEXT DEFAULT 'Pending',
        remarks TEXT,
        applied_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
     
    # =========================
    # Loans Document Table
    # ==============
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loans(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    loan_type TEXT,
    amount REAL,
    purpose TEXT,
    status TEXT DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS loan_documents(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER,
    document_type TEXT,
    file_path TEXT,
    status TEXT DEFAULT 'Pending'
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admins(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
    )
    """)   
     # Insert default admin
    cursor.execute("""
    INSERT OR IGNORE INTO admins(username,password)
    VALUES(?,?)
    """,
    (
        "admin",
        "admin123"
    ))  
         
         
    conn.commit()
    conn.close()

import database

database.create_database()

print("Database updated")

if __name__ == "__main__":
    create_database()
    print("✅ Database created successfully!")