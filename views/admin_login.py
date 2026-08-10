import customtkinter as ctk
from tkinter import messagebox
import sqlite3

from assets.ui_helpers import build_hero_header
from assets.icon_loader import get_icon
import security

ADMIN_ACCENT = "#0F172A"  # dark slate — visually distinct "admin mode"


class AdminLoginPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.master = master

        self.configure(fg_color="#F3F4F6")

        build_hero_header(
            self,
            title="SmartBank Admin",
            subtitle="Restricted access — authorized personnel only",
            icon_name="shield",
            accent_color=ADMIN_ACCENT,
            icon_size=44,
            height=120
        )

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True)

        card = ctk.CTkFrame(
            wrapper,
            corner_radius=20,
            fg_color="white",
            border_width=1,
            border_color="#E5E8EC",
            width=360
        )
        card.place(relx=0.5, rely=0.42, anchor="center")

        ctk.CTkLabel(
            card,
            text="Admin Login",
            font=("Arial", 20, "bold"),
            text_color="#111827"
        ).pack(pady=(30, 20), padx=40)

        self.username = ctk.CTkEntry(
            card,
            width=280,
            height=42,
            placeholder_text="👤  Admin Username"
        )
        self.username.pack(pady=8, padx=40)

        self.password = ctk.CTkEntry(
            card,
            width=280,
            height=42,
            placeholder_text="🔒  Admin Password",
            show="*"
        )
        self.password.pack(pady=8, padx=40)

        ctk.CTkButton(
            card,
            text="Login",
            width=280,
            height=42,
            fg_color=ADMIN_ACCENT,
            hover_color="#020617",
            command=self.login
        ).pack(pady=(20, 30), padx=40)

    def login(self):

        username = self.username.get().strip()
        password = self.password.get().strip()

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, password FROM admins WHERE username=?",
            (username,)
        )

        row = cursor.fetchone()

        conn.close()

        if row and security.verify_password(row[1], password):

            messagebox.showinfo(
                "Success",
                "Admin Login Successful!"
            )
            self.master.show_admin_dashboard()

        else:
            messagebox.showerror(
                "Login Failed",
                "Invalid Admin Credentials"
            )