import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import re
import session

from assets.ui_helpers import build_hero_header, PAGE_COLORS
from assets.icon_loader import get_icon


class TransferPage(ctk.CTkFrame):

    RECEIVER_CHECK_DEBOUNCE_MS = 500

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
        container.grid_rowconfigure((1, 2, 3, 4, 5, 6), weight=1)

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

        # ==========================
        # Receiver Username
        # ==========================
        self.receiver_entry = ctk.CTkEntry(
            container,
            width=350,
            height=45,
            placeholder_text="👤  Receiver Username"
        )
        self.receiver_entry.grid(row=2, column=0, pady=(10, 2))
        self.receiver_entry.bind("<KeyRelease>", self._on_receiver_typed)

        # Live "does this person exist" feedback -- debounced so we're
        # not hitting the DB on every keystroke.
        self.receiver_status_label = ctk.CTkLabel(
            container,
            text="",
            font=("Arial", 12),
            text_color="#6B7280"
        )
        self.receiver_status_label.grid(row=3, column=0, pady=(0, 8))
        self._receiver_check_after_id = None
        self._receiver_valid = False

        # ==========================
        # Amount
        # ==========================
        self.amount_entry = ctk.CTkEntry(
            container,
            width=350,
            height=45,
            placeholder_text="💵  Enter Amount"
        )
        self.amount_entry.grid(row=4, column=0, pady=10)
        self.amount_entry.bind("<KeyRelease>", self._sanitize_amount_input)
        self.amount_entry.bind("<Return>", lambda event: self.transfer_money())

        # ==========================
        # Inline status banner for submit-time feedback
        # ==========================
        self.status_label = ctk.CTkLabel(
            container,
            text="",
            font=("Arial", 13),
            text_color="#DC2626"
        )
        self.status_label.grid(row=5, column=0, pady=(0, 5))
        self._status_after_id = None

        # ==========================
        # Transfer Button
        # ==========================
        self.transfer_btn = ctk.CTkButton(
            container,
            text="Transfer",
            width=220,
            height=45,
            fg_color=PAGE_COLORS["transfer"],
            hover_color="#1D4ED8",
            command=self.transfer_money
        )
        self.transfer_btn.grid(row=6, column=0, pady=(15, 40))

    # -----------------------------------
    # Live receiver existence check (debounced)
    # -----------------------------------
    def _on_receiver_typed(self, event=None):

        self._receiver_valid = False

        if self._receiver_check_after_id:
            self.after_cancel(self._receiver_check_after_id)

        username = self.receiver_entry.get().strip()

        if not username:
            self.receiver_status_label.configure(text="")
            return

        self.receiver_status_label.configure(text="Checking...", text_color="#6B7280")

        self._receiver_check_after_id = self.after(
            self.RECEIVER_CHECK_DEBOUNCE_MS,
            lambda: self._check_receiver(username)
        )

    def _check_receiver(self, username):

        # The field may have changed since this was scheduled -- ignore
        # a stale check.
        if self.receiver_entry.get().strip() != username:
            return

        my_username = None
        try:
            my_username = session.current_user[2]
        except (TypeError, IndexError):
            pass

        if my_username and username.lower() == str(my_username).lower():
            self.receiver_status_label.configure(
                text="✗ You can't transfer to yourself", text_color="#DC2626"
            )
            self._receiver_valid = False
            return

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=?", (username,))
        found = cursor.fetchone()
        conn.close()

        if found:
            self.receiver_status_label.configure(text="✓ Valid recipient", text_color="#16A34A")
            self._receiver_valid = True
        else:
            self.receiver_status_label.configure(text="✗ User not found", text_color="#DC2626")
            self._receiver_valid = False

    # -----------------------------------
    # Live amount sanitization
    # -----------------------------------
    def _sanitize_amount_input(self, event=None):
        raw = self.amount_entry.get()

        cleaned = re.sub(r"[^0-9.]", "", raw)
        parts = cleaned.split(".")
        if len(parts) > 2:
            cleaned = parts[0] + "." + "".join(parts[1:])

        if cleaned != raw:
            cursor_pos = self.amount_entry.index("insert")
            self.amount_entry.delete(0, "end")
            self.amount_entry.insert(0, cleaned)
            self.amount_entry.icursor(min(cursor_pos, len(cleaned)))

        if cleaned:
            self._clear_status()

    # -----------------------------------
    # Inline status helpers
    # -----------------------------------
    def _show_status(self, message, kind="error"):
        color = "#16A34A" if kind == "success" else "#DC2626"
        self.status_label.configure(text=message, text_color=color)

        if self._status_after_id:
            self.after_cancel(self._status_after_id)

        self._status_after_id = self.after(4000, self._clear_status)

    def _clear_status(self):
        self.status_label.configure(text="")
        self._status_after_id = None

    # -----------------------------------
    # Transfer action
    # -----------------------------------
    def transfer_money(self):

        receiver_username = self.receiver_entry.get().strip()
        amount_text = self.amount_entry.get().strip()

        if receiver_username == "" or amount_text == "":
            self._show_status("Please fill all fields.")
            return

        try:
            amount = round(float(amount_text), 2)
        except ValueError:
            self._show_status("Please enter a valid amount.")
            return

        if amount <= 0:
            self._show_status("Amount must be greater than zero.")
            return

        # The live check already caught the common cases (typo'd
        # username, self-transfer) before they even hit submit -- but
        # we still re-verify against the DB below right before writing,
        # since the live check can go stale (e.g. that account could
        # theoretically be deleted between the check and submit).

        self.transfer_btn.configure(state="disabled", text="Transferring...")
        self.update_idletasks()

        try:
            conn = sqlite3.connect("bank.db")
            cursor = conn.cursor()

            sender_id = session.current_user[0]

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
                messagebox.showerror("Error", "Sender not found.")
                return

            sender_balance = sender[0]

            if sender_balance < amount:
                conn.close()
                self._show_status(
                    f"Insufficient balance — you have ₹{sender_balance:,.2f} available."
                )
                return

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
                self._show_status(f"No user found with username '{receiver_username}'.")
                return

            receiver_id = receiver[0]

            if receiver_id == sender_id:
                conn.close()
                self._show_status("You cannot transfer money to yourself.")
                return

            cursor.execute(
                """
                UPDATE users
                SET balance = balance - ?
                WHERE id=?
                """,
                (amount, sender_id)
            )

            cursor.execute(
                """
                UPDATE users
                SET balance = balance + ?
                WHERE id=?
                """,
                (amount, receiver_id)
            )

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

            new_balance = round(sender_balance - amount, 2)

            current = list(session.current_user)
            current[4] = new_balance
            session.current_user = tuple(current)

            self._show_status(
                f"₹{amount:,.2f} sent to {receiver_username}! New balance: ₹{new_balance:,.2f}",
                kind="success"
            )

            self.receiver_entry.delete(0, "end")
            self.amount_entry.delete(0, "end")
            self.receiver_status_label.configure(text="")
            self._receiver_valid = False

            self.after(900, self._go_to_dashboard)

        finally:
            self.transfer_btn.configure(state="normal", text="Transfer")

    def _go_to_dashboard(self):
        self.master.master.show_dashboard()