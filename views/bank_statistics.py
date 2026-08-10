import customtkinter as ctk
import sqlite3

from assets.ui_helpers import build_hero_header
from assets.icon_loader import get_icon

STATS_ACCENT = "#9333EA"


class BankStatisticsPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.master = master

        self.configure(fg_color="#F9FAFB")
        self.pack(fill="both", expand=True)

        build_hero_header(
            self,
            title="Bank Statistics",
            subtitle="A live overview of SmartBank's performance",
            icon_name="chart_up",
            accent_color=STATS_ACCENT,
            icon_size=40,
            height=100
        )

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        # -------------------------
        # Back Button
        # -------------------------
        ctk.CTkButton(
            wrapper,
            text="⬅ Back to Dashboard",
            width=180,
            fg_color="transparent",
            border_width=1,
            border_color="#D1D5DB",
            text_color="#374151",
            hover_color="#F3F4F6",
            command=self.go_back
        ).pack(anchor="w", pady=(0, 15))

        self.cards = ctk.CTkScrollableFrame(wrapper, fg_color="transparent")
        self.cards.pack(fill="both", expand=True)

        for i in range(3):
            self.cards.grid_rowconfigure(i, weight=1)

        for i in range(2):
            self.cards.grid_columnconfigure(i, weight=1)

        self.load_statistics()

    # ------------------------
    # Create Statistic Card (colored strip + icon badge, matches Dashboard style)
    # ------------------------

    def statistic_card(self, row, column, title, value, icon_name, accent, accent_bg):

        frame = ctk.CTkFrame(
            self.cards,
            corner_radius=15,
            fg_color="white",
            border_width=1,
            border_color="#E5E8EC"
        )

        frame.grid(row=row, column=column, padx=15, pady=15, sticky="nsew")

        ctk.CTkFrame(frame, height=6, corner_radius=0, fg_color=accent).pack(fill="x", side="top")

        badge = ctk.CTkFrame(frame, width=48, height=48, corner_radius=24, fg_color=accent_bg)
        badge.pack(pady=(20, 10))
        badge.pack_propagate(False)

        icon_img = get_icon(icon_name, size=22)
        if icon_img:
            ctk.CTkLabel(badge, image=icon_img, text="").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            frame,
            text=title.upper(),
            font=("Arial", 12, "bold"),
            text_color="#6B7280"
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            frame,
            text=value,
            font=("Arial", 24, "bold"),
            text_color="#111827"
        ).pack(pady=(0, 22))

    # ------------------------
    # Load Statistics
    # ------------------------

    def load_statistics(self):

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT IFNULL(SUM(balance),0) FROM users")
        total_balance = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM transactions")
        total_transactions = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM loans WHERE status='Pending'")
        pending = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM loans WHERE status='Approved'")
        approved = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM loans WHERE status='Rejected'")
        rejected = cursor.fetchone()[0]

        conn.close()

        self.statistic_card(0, 0, "Total Users", str(total_users),
                             "bust", "#1E3A8A", "#DBEAFE")
        self.statistic_card(0, 1, "Total Balance", f"₹{total_balance:,.2f}",
                             "money_bag", "#16A34A", "#DCFCE7")
        self.statistic_card(1, 0, "Transactions", str(total_transactions),
                             "scroll", "#2563EB", "#DBEAFE")
        self.statistic_card(1, 1, "Pending Loans", str(pending),
                             "credit_card", "#D97706", "#FEF3C7")
        self.statistic_card(2, 0, "Approved Loans", str(approved),
                             "credit_card", "#16A34A", "#DCFCE7")
        self.statistic_card(2, 1, "Rejected Loans", str(rejected),
                             "credit_card", "#DC2626", "#FEE2E2")

    # ------------------------
    # Back to Dashboard
    # ------------------------

    def go_back(self):
        self.master.show_admin_dashboard()
