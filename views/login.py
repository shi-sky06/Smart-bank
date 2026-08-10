import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import session
from views.admin_login import AdminLoginPage

from assets.ui_helpers import build_hero_header, PAGE_COLORS
from assets.icon_loader import get_icon
import security


class LoginPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.master = master

        self.configure(fg_color="#F3F4F6")

        # =========================
        # Hero Header (logo + brand)
        # =========================
        build_hero_header(
            self,
            title="SmartBank AI",
            subtitle="Secure Digital Banking, Powered by AI",
            icon_name="bank_logo",
            accent_color=PAGE_COLORS["login"],
            icon_size=48,
            height=130
        )

        # =========================
        # Centered Login Card
        # =========================
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True)

        card = ctk.CTkFrame(
            wrapper,
            corner_radius=20,
            fg_color="white",
            border_width=1,
            border_color="#E5E8EC",
            width=380
        )
        card.place(relx=0.5, rely=0.4, anchor="center")

        ctk.CTkLabel(
            card,
            text="Welcome Back",
            font=("Arial", 22, "bold"),
            text_color="#111827"
        ).pack(pady=(30, 2), padx=40)

        ctk.CTkLabel(
            card,
            text="Login to continue to your account",
            font=("Arial", 13),
            text_color="#6B7280"
        ).pack(pady=(0, 20), padx=40)

        self.username = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="👤  Username"
        )
        self.username.pack(pady=8, padx=40)

        self.password = ctk.CTkEntry(
            card,
            width=300,
            height=42,
            placeholder_text="🔒  Password",
            show="*"
        )
        self.password.pack(pady=8, padx=40)

        ctk.CTkButton(
            card,
            text="Login",
            width=300,
            height=42,
            fg_color=PAGE_COLORS["login"],
            hover_color="#152C69",
            command=self.login
        ).pack(pady=(18, 10), padx=40)

        ctk.CTkButton(
            card,
            text="🛡️  Admin Login",
            width=300,
            height=38,
            fg_color="transparent",
            border_width=1,
            border_color="#D1D5DB",
            text_color="#374151",
            hover_color="#F3F4F6",
            command=self.open_admin
        ).pack(pady=6, padx=40)

        ctk.CTkButton(
            card,
            text="Create Account",
            width=300,
            height=36,
            fg_color="transparent",
            text_color=PAGE_COLORS["login"],
            hover_color="#F3F4F6",
            command=master.show_register
        ).pack(pady=(6, 30), padx=40)

    def login(self):

        username = self.username.get()
        password = self.password.get()

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if user and security.verify_password(user[3], password):

            session.current_user = user

            print("Logged in user:", session.current_user)

            messagebox.showinfo(
                "Success",
                "Login Successful!"
            )

            self.master.show_app()

        else:

            messagebox.showerror(
                "Error",
                "Invalid Username or Password"
            )

    def open_admin(self):

        self.master.show_admin_login()

    