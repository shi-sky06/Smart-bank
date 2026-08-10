import customtkinter as ctk
import sqlite3
from tkinter import ttk

class AdminTransactionsPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.pack(fill="both", expand=True, padx=20, pady=20)

        # -------------------------
        # Back Button
        # -------------------------
        ctk.CTkButton(
            self,
            text="⬅ Back to Dashboard",
            width=180,
            command=self.go_back
        ).pack(anchor="w", pady=(5, 10))

        # -------------------------
        # Title
        # -------------------------
        title = ctk.CTkLabel(
            self,
            text="📜 Transaction History",
            font=("Arial", 26, "bold")
        )
        title.pack(pady=10)

        # -------------------------
        # Search Frame
        # -------------------------
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", pady=10)

        self.search_entry = ctk.CTkEntry(
            top_frame,
            width=250,
            placeholder_text="Search Username"
        )
        self.search_entry.pack(side="left", padx=10)

        ctk.CTkButton(
            top_frame,
            text="🔍 Search",
            command=self.search_transactions
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            top_frame,
            text="🔄 Refresh",
            command=self.load_transactions
        ).pack(side="left", padx=5)

        # -------------------------
        # Table
        # -------------------------
        columns = (
            "ID",
            "Username",
            "Type",
            "Receiver",
            "Amount",
            "Date"
        )

        self.tree = ttk.Treeview(
            self,
            columns=columns,
            show="headings",
            height=18
        )

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=150)

        scrollbar = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.total_label = ctk.CTkLabel(
            self,
            text=""
        )
        self.total_label.pack(pady=10)

        self.load_transactions()

    def load_transactions(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            transactions.id,
            users.username,
            transactions.transaction_type,
            transactions.receiver,
            transactions.amount,
            transactions.date
        FROM transactions
        JOIN users
        ON users.id = transactions.user_id
        ORDER BY transactions.date DESC
        """)

        rows = cursor.fetchall()

        for row in rows:
            self.tree.insert("", "end", values=row)

        self.total_label.configure(
            text=f"Total Transactions : {len(rows)}"
        )

        conn.close()

    def search_transactions(self):

        username = self.search_entry.get().strip()

        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            transactions.id,
            users.username,
            transactions.transaction_type,
            transactions.receiver,
            transactions.amount,
            transactions.date
        FROM transactions
        JOIN users
        ON users.id = transactions.user_id
        WHERE users.username LIKE ?
        ORDER BY transactions.date DESC
        """, (f"%{username}%",))

        rows = cursor.fetchall()

        for row in rows:
            self.tree.insert("", "end", values=row)

        self.total_label.configure(
            text=f"Results : {len(rows)}"
        )
    
        conn.close()
        
        # -------------------------
# Back to Admin Dashboard
# -------------------------

    def go_back(self):
        self.master.show_admin_dashboard()
    
    
    