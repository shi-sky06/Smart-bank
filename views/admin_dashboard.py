import customtkinter as ctk
from tkinter import messagebox

from assets.ui_helpers import build_hero_header
from assets.icon_loader import get_icon

ADMIN_ACCENT = "#0F172A"


class AdminDashboardPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.master = master

        self.configure(fg_color="#F9FAFB")

        # Layout
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure((1, 2, 3), weight=1)

        # Hero Header (replaces old title + welcome text)
        hero_wrap = ctk.CTkFrame(self, fg_color="transparent")
        hero_wrap.grid(row=0, column=0, columnspan=2, sticky="ew", padx=30, pady=(25, 5))

        build_hero_header(
            hero_wrap,
            title="SmartBank Admin Dashboard",
            subtitle="Welcome back, Administrator",
            icon_name="shield",
            accent_color=ADMIN_ACCENT,
            icon_size=44,
            height=110
        )

        # Action cards — each with icon + distinct accent color
        actions = [
            ("Manage Users", "bust", "#1E3A8A", self.open_manage_users),
            ("Loan Verification", "credit_card", "#9333EA", self.loan_verification),
            ("Document Verification", "scroll", "#D97706", self.document_verification),
            ("View Transactions", "bar_chart", "#2563EB", self.open_transactions),
            ("Bank Statistics", "chart_up", "#16A34A", self.bank_statistics),
            ("Logout", None, "#DC2626", self.logout),
        ]

        positions = [(1, 0), (1, 1), (2, 0), (2, 1), (3, 0), (3, 1)]

        for (label, icon_name, color, command), (row, col) in zip(actions, positions):
            icon_img = get_icon(icon_name, size=20) if icon_name else None

            btn = ctk.CTkButton(
                self,
                text=f"  {label}",
                image=icon_img,
                compound="left",
                width=260,
                height=54,
                corner_radius=14,
                fg_color=color,
                hover_color=self._darken(color),
                font=("Arial", 15, "bold")
            )
            btn.configure(command=command)
            btn.grid(row=row, column=col, padx=20, pady=15)

    @staticmethod
    def _darken(hex_color):
        # Simple darken for hover states
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        factor = 0.8
        return f"#{int(r * factor):02x}{int(g * factor):02x}{int(b * factor):02x}"

    def open_manage_users(self):
        self.master.show_manage_users()

    def loan_verification(self):
        self.master.show_loan_verification()

    def document_verification(self):
        self.master.show_document_verification()

    def open_transactions(self):
        self.master.show_admin_transactions()

    def bank_statistics(self):
        self.master.show_bank_statistics()

    def logout(self):
        self.master.show_login()