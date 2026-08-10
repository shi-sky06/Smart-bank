import customtkinter as ctk
from tkinter import messagebox
import sqlite3

from assets.ui_helpers import build_hero_header, PAGE_COLORS
import security


class RegisterPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="#F3F4F6")

        # =========================
        # Hero Header (logo + brand)
        # =========================
        build_hero_header(
            self,
            title="Create New Account",
            subtitle="Join SmartBank AI in minutes",
            icon_name="bank_logo",
            accent_color=PAGE_COLORS["register"],
            icon_size=44,
            height=110
        )

        # =========================
        # Centered Register Card (scrollable — more fields than login)
        # =========================
        wrapper = ctk.CTkScrollableFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True)
        wrapper.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            wrapper,
            corner_radius=20,
            fg_color="white",
            border_width=1,
            border_color="#E5E8EC",
            width=380
        )
        card.grid(row=0, column=0, pady=20)

        self.name = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="🧑  Full Name"
        )
        self.name.pack(pady=(30, 8), padx=40)

        self.username = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="👤  Username"
        )
        self.username.pack(pady=8, padx=40)

        # Gmail field
        self.email = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="✉️  Gmail Address"
        )
        self.email.pack(pady=8, padx=40)

        self.password = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="🔒  Password",
            show="*"
        )
        self.password.pack(pady=8, padx=40)

        self.confirm = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="🔒  Confirm Password",
            show="*"
        )
        self.confirm.pack(pady=8, padx=40)

        self.balance = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="💰  Initial Balance"
        )
        self.balance.pack(pady=8, padx=40)

        ctk.CTkButton(
            card,
            text="Create Account",
            width=300,
            height=42,
            fg_color=PAGE_COLORS["register"],
            hover_color="#152C69",
            command=self.register
        ).pack(pady=(18, 10), padx=40)

        ctk.CTkButton(
            card,
            text="← Back to Login",
            width=300,
            height=36,
            fg_color="transparent",
            text_color=PAGE_COLORS["register"],
            hover_color="#F3F4F6",
            command=master.show_login
        ).pack(pady=(6, 30), padx=40)

    def register(self):

        name = self.name.get()
        username = self.username.get()
        email = self.email.get()
        password = self.password.get()
        confirm = self.confirm.get()
        balance = self.balance.get()

        # Check empty fields
        if "" in [name, username, email, password, confirm, balance]:
            messagebox.showerror(
                "Error",
                "Please fill all fields."
            )
            return

        # Check Gmail format
        if not email.endswith("@gmail.com"):
            messagebox.showerror(
                "Error",
                "Please enter a valid Gmail address."
            )
            return

        # Check password match
        if password != confirm:
            messagebox.showerror(
                "Error",
                "Passwords do not match."
            )
            return

        # Convert balance
        try:
            balance = float(balance)
        except ValueError:
            messagebox.showerror(
                "Error",
                "Balance must be a number."
            )
            return

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        # Check username already exists
        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        if cursor.fetchone():
            messagebox.showerror(
                "Error",
                "Username already exists."
            )
            conn.close()
            return

        # Insert user with email (plaintext password, per current settings)
        cursor.execute(
            """
            INSERT INTO users(name, username, email, password, balance)
            VALUES(?,?,?,?,?)
            """,
            (name, username, email, password, balance)
        )

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Success",
            "Account created successfully!"
        )

        self.master.show_login()