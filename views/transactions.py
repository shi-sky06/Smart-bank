import customtkinter as ctk
import sqlite3
import session

from assets.ui_helpers import build_hero_header, PAGE_COLORS
from assets.icon_loader import get_icon


class TransactionsPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="transparent")

        # Hero Header
        build_hero_header(
            self,
            title="Transaction History",
            subtitle="A record of your recent account activity",
            icon_name="scroll",
            accent_color=PAGE_COLORS["transactions"],
            icon_size=40,
            height=100
        )

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=40, pady=(0, 30))

        card = ctk.CTkFrame(wrapper, corner_radius=15)
        card.pack(fill="both", expand=True)

        # Color strip
        ctk.CTkFrame(
            card, height=6, corner_radius=0, fg_color=PAGE_COLORS["transactions"]
        ).pack(fill="x", side="top")

        self.transaction_box = ctk.CTkTextbox(
            card,
            font=("Arial", 15),
            wrap="word"
        )
        self.transaction_box.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # Color tags for transaction types
        self.transaction_box.tag_config("deposit", foreground="#16A34A")
        self.transaction_box.tag_config("withdraw", foreground="#DC2626")
        self.transaction_box.tag_config("transfer", foreground="#2563EB")
        self.transaction_box.tag_config("default", foreground="#374151")
        self.transaction_box.tag_config("muted", foreground="#6B7280")

        self.load_transactions()

    def load_transactions(self):

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        user_id = session.current_user[0]

        cursor.execute(
            """
            SELECT transaction_type, receiver, amount, date
            FROM transactions
            WHERE user_id=?
            ORDER BY date DESC
            """,
            (user_id,)
        )

        transactions = cursor.fetchall()

        conn.close()

        if not transactions:

            self.transaction_box.insert(
                "end",
                "No transactions found."
            )

            return

        for transaction in transactions:

            transaction_type = transaction[0]
            receiver = transaction[1]
            amount = transaction[2]
            date = transaction[3]

            type_clean = str(transaction_type).strip().lower()

            if "deposit" in type_clean:
                tag = "deposit"
                icon = "⬆️ "
            elif "withdraw" in type_clean:
                tag = "withdraw"
                icon = "⬇️ "
            elif "transfer" in type_clean:
                tag = "transfer"
                icon = "🔄 "
            else:
                tag = "default"
                icon = "• "

            self.transaction_box.insert(
                "end", f"{icon}Type: {transaction_type}\n", tag
            )
            self.transaction_box.insert(
                "end", f"Receiver: {receiver if receiver else '-'}\n", "muted"
            )
            self.transaction_box.insert(
                "end", f"Amount: ₹{amount:.2f}\n", tag
            )
            self.transaction_box.insert(
                "end", f"Date: {date}\n", "muted"
            )
            self.transaction_box.insert(
                "end", "-----------------------------\n\n", "muted"
            )

        self.transaction_box.configure(state="disabled")
