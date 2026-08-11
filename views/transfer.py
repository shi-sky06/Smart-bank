import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import session

from assets.ui_helpers import build_hero_header, PAGE_COLORS
from assets.icon_loader import get_icon


class TransferPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="transparent")

        # ==========================
        # Layout
        # ==========================
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Hero Header
        hero_wrap = ctk.CTkFrame(self, fg_color="transparent")
        hero_wrap.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 0))

        build_hero_header(
            hero_wrap,
            title="Transfer Money",
            subtitle="Send money to another SmartBank user",
            icon_name="repeat",
            accent_color=PAGE_COLORS["transfer"],
            icon_size=40,
            height=100
        )

        container = ctk.CTkFrame(self, corner_radius=15)
        container.grid(row=1, column=0, padx=40, pady=(10, 40), sticky="nsew")
        container.grid_columnconfigure(0, weight=1)

        # Color strip
        ctk.CTkFrame(
            container, height=6, corner_radius=0, fg_color=PAGE_COLORS["transfer"]
        ).grid(row=0, column=0, sticky="ew")

        # Title with icon
        title_row = ctk.CTkFrame(container, fg_color="transparent")
        title_row.grid(row=1, column=0, pady=(35, 20))

        icon_img = get_icon("repeat", size=26)
        if icon_img:
            ctk.CTkLabel(title_row, image=icon_img, text="").pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            title_row,
            text="Transfer Money",
            font=("Arial", 26, "bold")
        ).pack(side="left")

        # Receiver Username
        self.receiver_entry = ctk.CTkEntry(
            container,
            width=350,
            height=45,
            placeholder_text="👤  Receiver Username"
        )
        self.receiver_entry.grid(row=2, column=0, pady=10)

        # Amount
        self.amount_entry = ctk.CTkEntry(
            container,
            width=350,
            height=45,
            placeholder_text="💵  Enter Amount"
        )
        self.amount_entry.grid(row=3, column=0, pady=10)

        # Transfer Button
        ctk.CTkButton(
            container,
            text="Transfer",
            width=220,
            height=45,
            fg_color=PAGE_COLORS["transfer"],
            hover_color="#1D4ED8",
            command=self.transfer_money
        ).grid(row=4, column=0, pady=(15, 40))

    def transfer_money(self):

        receiver_username = self.receiver_entry.get().strip()
        amount = self.amount_entry.get().strip()

        if receiver_username == "" or amount == "":
            messagebox.showerror(
                "Error",
                "Please fill all fields."
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

            sender_id = session.current_user[0]

            # Get sender balance
            cursor.execute(
                """
                SELECT balance
                FROM users
                WHERE id=?
                """,
                (sender_id,)
            )

            sender = cursor.fetchone()

            if sender is None:
                conn.close()
                messagebox.showerror(
                    "Error",
                    "Sender not found."
                )
                return

            sender_balance = sender[0]

            if sender_balance < amount:
                conn.close()
                messagebox.showerror(
                    "Error",
                    "Insufficient balance."
                )
                return

            # Find receiver
            cursor.execute(
                """
                SELECT id
                FROM users
                WHERE username=?
                """,
                (receiver_username,)
            )

            receiver = cursor.fetchone()

            if receiver is None:
                conn.close()
                messagebox.showerror(
                    "Error",
                    "Receiver not found."
                )
                return

            receiver_id = receiver[0]

            if receiver_id == sender_id:
                conn.close()
                messagebox.showerror(
                    "Error",
                    "You cannot transfer money to yourself."
                )
                return

            # Deduct sender balance
            cursor.execute(
                """
                UPDATE users
                SET balance = balance - ?
                WHERE id=?
                """,
                (amount, sender_id)
            )

            # Credit receiver balance
            cursor.execute(
                """
                UPDATE users
                SET balance = balance + ?
                WHERE id=?
                """,
                (amount, receiver_id)
            )

            # Record transaction
            cursor.execute(
                """
                INSERT INTO transactions
                (user_id, transaction_type, receiver, amount)
                VALUES (?, ?, ?, ?)
                """,
                (
                    sender_id,
                    "Transfer",
                    receiver_username,
                    amount
                )
            )

            conn.commit()
            conn.close()

            # Update session balance
            new_balance = sender_balance - amount

            # Update session balance
            new_balance = sender_balance - amount

            current = list(session.current_user)
            current[4] = new_balance
            session.current_user = tuple(current)

            messagebox.showinfo(
                "Success",
                f"₹{amount:,.2f} transferred successfully!"
            )

            self.receiver_entry.delete(0, "end")
            self.amount_entry.delete(0, "end")

            self.master.master.show_dashboard()

        except ValueError:
            messagebox.showerror(
                "Error",
                "Please enter a valid amount."
            )
