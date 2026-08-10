import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import session

from assets.ui_helpers import build_hero_header, PAGE_COLORS
from assets.icon_loader import get_icon


class DepositPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="transparent")

        # ==========================
        # Responsive Layout
        # ==========================
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Hero Header
        hero_wrap = ctk.CTkFrame(self, fg_color="transparent")
        hero_wrap.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 0))

        build_hero_header(
            hero_wrap,
            title="Deposit Money",
            subtitle="Add funds to your account instantly",
            icon_name="money_bag",
            accent_color=PAGE_COLORS["deposit"],
            icon_size=40,
            height=100
        )

        container = ctk.CTkFrame(self, corner_radius=15)
        container.grid(row=1, column=0, padx=40, pady=(10, 40), sticky="nsew")

        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure((1, 2, 3), weight=1)

        # Color strip
        ctk.CTkFrame(
            container, height=6, corner_radius=0, fg_color=PAGE_COLORS["deposit"]
        ).grid(row=0, column=0, sticky="ew")

        # ==========================
        # Title with icon
        # ==========================
        title_row = ctk.CTkFrame(container, fg_color="transparent")
        title_row.grid(row=1, column=0, pady=(35, 20))

        icon_img = get_icon("money_bag", size=26)
        if icon_img:
            ctk.CTkLabel(title_row, image=icon_img, text="").pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            title_row,
            text="Deposit Money",
            font=("Arial", 26, "bold")
        ).pack(side="left")

        # ==========================
        # Amount Entry
        # ==========================
        self.amount_entry = ctk.CTkEntry(
            container,
            width=350,
            height=45,
            placeholder_text="💵  Enter Deposit Amount"
        )
        self.amount_entry.grid(row=2, column=0, pady=20)

        # ==========================
        # Deposit Button
        # ==========================
        deposit_btn = ctk.CTkButton(
            container,
            text="Deposit",
            width=220,
            height=45,
            fg_color=PAGE_COLORS["deposit"],
            hover_color="#15803D",
            command=self.deposit_money
        )
        deposit_btn.grid(row=3, column=0, pady=(0, 40))

    def deposit_money(self):

        amount = self.amount_entry.get().strip()

        if amount == "":
            messagebox.showerror(
                "Error",
                "Enter an amount."
            )
            return

        try:
            amount = float(amount)

            if amount <= 0:
                messagebox.showerror(
                    "Error",
                    "Amount must be greater than zero."
                )
                return

            conn = sqlite3.connect("bank.db")
            cursor = conn.cursor()

            user_id = session.current_user[0]

            cursor.execute(
                "SELECT balance FROM users WHERE id=?",
                (user_id,)
            )

            user = cursor.fetchone()

            if user is None:
                conn.close()
                messagebox.showerror(
                    "Error",
                    "User not found."
                )
                return

            current_balance = user[0]
            new_balance = current_balance + amount

            cursor.execute(
                """
                UPDATE users
                SET balance=?
                WHERE id=?
                """,
                (new_balance, user_id)
            )

            cursor.execute(
                """
                INSERT INTO transactions
                (user_id, transaction_type, receiver, amount)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    "Deposit",
                    None,
                    amount
                )
            )

            conn.commit()
            conn.close()

            session.current_user = (
                session.current_user[0],
                session.current_user[1],
                session.current_user[2],
                session.current_user[3],
                new_balance
            )

            messagebox.showinfo(
                "Success",
                f"₹{amount:,.2f} deposited successfully!"
            )

            self.amount_entry.delete(0, "end")

            # Refresh Dashboard
            self.master.master.show_dashboard()

        except ValueError:
            messagebox.showerror(
                "Error",
                "Please enter a valid amount."
            )
