import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import session

from assets.ui_helpers import build_hero_header, PAGE_COLORS
from assets.icon_loader import get_icon


class WithdrawPage(ctk.CTkFrame):

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
            title="Withdraw Money",
            subtitle="Take cash out of your account",
            icon_name="down_arrow",
            accent_color=PAGE_COLORS["withdraw"],
            icon_size=40,
            height=100
        )

        container = ctk.CTkFrame(self, corner_radius=15)
        container.grid(row=1, column=0, padx=40, pady=(10, 40), sticky="nsew")
        container.grid_columnconfigure(0, weight=1)

        # Color strip at top of card
        ctk.CTkFrame(
            container, height=6, corner_radius=0, fg_color=PAGE_COLORS["withdraw"]
        ).grid(row=0, column=0, sticky="ew")

        # Title with icon
        title_row = ctk.CTkFrame(container, fg_color="transparent")
        title_row.grid(row=1, column=0, pady=(35, 20))

        icon_img = get_icon("down_arrow", size=26)
        if icon_img:
            ctk.CTkLabel(title_row, image=icon_img, text="").pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            title_row,
            text="Withdraw Money",
            font=("Arial", 26, "bold")
        ).pack(side="left")

        # Amount Entry
        self.amount_entry = ctk.CTkEntry(
            container,
            width=350,
            height=45,
            placeholder_text="💵  Enter Withdrawal Amount"
        )
        self.amount_entry.grid(row=2, column=0, pady=20)

        # Withdraw Button
        ctk.CTkButton(
            container,
            text="Withdraw",
            width=220,
            height=45,
            fg_color=PAGE_COLORS["withdraw"],
            hover_color="#B91C1C",
            command=self.withdraw_money
        ).grid(row=3, column=0, pady=(0, 40))

    def withdraw_money(self):

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

            # Logged in user
            user_id = session.current_user[0]

            # Get current balance
            cursor.execute(
                """
                SELECT balance
                FROM users
                WHERE id=?
                """,
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

            if amount > current_balance:
                conn.close()
                messagebox.showerror(
                    "Error",
                    "Insufficient balance."
                )
                return

            new_balance = current_balance - amount

            # Update balance
            cursor.execute(
                """
                UPDATE users
                SET balance=?
                WHERE id=?
                """,
                (new_balance, user_id)
            )

            # Save transaction
            cursor.execute(
                """
                INSERT INTO transactions
                (user_id, transaction_type, receiver, amount)
                VALUES (?, ?, ?, ?)
                """,
                (
                    user_id,
                    "Withdraw",
                    None,
                    amount
                )
            )

            conn.commit()
            conn.close()

            # Update session balance
            session.current_user = (
                session.current_user[0],
                session.current_user[1],
                session.current_user[2],
                session.current_user[3],
                new_balance
            )

            messagebox.showinfo(
                "Success",
                f"₹{amount:,.2f} withdrawn successfully!"
            )

            self.amount_entry.delete(0, "end")

            # Return to dashboard
            self.master.master.show_dashboard()

        except ValueError:
            messagebox.showerror(
                "Error",
                "Please enter a valid amount."
            )
