import customtkinter as ctk
from tkinter import messagebox
import threading
import sqlite3

import session
from assets.ui_helpers import build_hero_header, PAGE_COLORS
from assets.icon_loader import get_icon
from fx_rates import CURRENCIES, get_rate

FEE_PERCENT = 1.5  # simulated flat international transfer fee
BASE_CURRENCY = "INR"  # matches the ₹ balances already stored in bank.db

COUNTRIES = [
    "United States", "United Kingdom", "Germany", "France", "Japan",
    "Australia", "Canada", "China", "Singapore", "United Arab Emirates"
]

COUNTRY_TO_CURRENCY = {
    "United States": "USD",
    "United Kingdom": "GBP",
    "Germany": "EUR",
    "France": "EUR",
    "Japan": "JPY",
    "Australia": "AUD",
    "Canada": "CAD",
    "China": "CNY",
    "Singapore": "SGD",
    "United Arab Emirates": "AED",
}


class InternationalTransferPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="transparent")

        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        hero_wrap = ctk.CTkFrame(self, fg_color="transparent")
        hero_wrap.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 0))

        build_hero_header(
            hero_wrap,
            title="International Transfer",
            subtitle="Send money abroad — converted at live exchange rates",
            icon_name="repeat",
            accent_color=PAGE_COLORS.get("transfer", "#1E3A8A"),
            icon_size=40,
            height=100
        )

        container = ctk.CTkFrame(self, corner_radius=15)
        container.grid(row=1, column=0, padx=40, pady=(10, 40), sticky="nsew")
        container.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(
            container, height=6, corner_radius=0, fg_color=PAGE_COLORS.get("transfer", "#1E3A8A")
        ).grid(row=0, column=0, sticky="ew")

        title_row = ctk.CTkFrame(container, fg_color="transparent")
        title_row.grid(row=1, column=0, pady=(35, 15))

        icon_img = get_icon("repeat", size=26)
        if icon_img:
            ctk.CTkLabel(title_row, image=icon_img, text="").pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            title_row, text="International Transfer", font=("Arial", 26, "bold")
        ).pack(side="left")

        self.recipient_entry = ctk.CTkEntry(
            container, width=350, height=45, placeholder_text="👤  Recipient Name"
        )
        self.recipient_entry.grid(row=2, column=0, pady=10)

        self.country_var = ctk.StringVar(value=COUNTRIES[0])
        ctk.CTkOptionMenu(
            container, values=COUNTRIES, variable=self.country_var,
            width=350, command=self._on_country_change
        ).grid(row=3, column=0, pady=10)

        amount_row = ctk.CTkFrame(container, fg_color="transparent")
        amount_row.grid(row=4, column=0, pady=10)

        self.amount_entry = ctk.CTkEntry(
            amount_row, width=230, height=45, placeholder_text="💵  Amount to Send"
        )
        self.amount_entry.pack(side="left", padx=(0, 10))

        self.currency_var = ctk.StringVar(value=COUNTRY_TO_CURRENCY[COUNTRIES[0]])
        self.currency_menu = ctk.CTkOptionMenu(
            amount_row, values=CURRENCIES, variable=self.currency_var, width=100
        )
        self.currency_menu.pack(side="left")

        self.preview_button = ctk.CTkButton(
            container, text="Preview Conversion", width=250, height=42,
            fg_color="transparent", border_width=1, border_color="#D1D5DB",
            text_color="#374151", hover_color="#F3F4F6",
            command=self.preview
        )
        self.preview_button.grid(row=5, column=0, pady=(15, 5))

        self.preview_label = ctk.CTkLabel(
            container, text="", font=("Arial", 13), text_color="#6B7280",
            justify="center"
        )
        self.preview_label.grid(row=6, column=0, pady=(0, 10))

        self.send_button = ctk.CTkButton(
            container, text="Send Internationally", width=250, height=45,
            fg_color=PAGE_COLORS.get("transfer", "#1E3A8A"), hover_color="#1D4ED8",
            command=self.send_money
        )
        self.send_button.grid(row=7, column=0, pady=(10, 40))

    def _on_country_change(self, country):
        self.currency_var.set(COUNTRY_TO_CURRENCY.get(country, "USD"))

    def preview(self):
        amount_text = self.amount_entry.get().strip()

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount greater than zero.")
            return

        self.preview_button.configure(state="disabled", text="Calculating...")

        threading.Thread(
            target=self._do_preview, args=(amount, self.currency_var.get()), daemon=True
        ).start()

    def _do_preview(self, amount, to_currency):
        rate, source = get_rate(BASE_CURRENCY, to_currency)
        # rate converts BASE -> to_currency; we need the inverse
        # (amount in to_currency -> BASE), so divide instead of multiply
        base_equivalent = amount / rate
        fee = base_equivalent * (FEE_PERCENT / 100)
        total = base_equivalent + fee

        self.after(0, lambda: self._show_preview(amount, to_currency, base_equivalent, fee, total, source))

    def _show_preview(self, amount, to_currency, base_equivalent, fee, total, source):
        self.preview_label.configure(
            text=(
                f"{amount:,.2f} {to_currency} ≈ ₹{base_equivalent:,.2f}\n"
                f"Transfer fee ({FEE_PERCENT}%): ₹{fee:,.2f}\n"
                f"Total deducted: ₹{total:,.2f}\n"
                f"{source}"
            )
        )
        self.preview_button.configure(state="normal", text="Preview Conversion")

    def send_money(self):

        recipient = self.recipient_entry.get().strip()
        country = self.country_var.get()
        amount_text = self.amount_entry.get().strip()

        if not recipient or not amount_text:
            messagebox.showerror("Error", "Please fill all fields.")
            return

        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount.")
            return

        self.send_button.configure(state="disabled", text="Sending...")

        threading.Thread(
            target=self._do_send,
            args=(recipient, country, amount, self.currency_var.get()),
            daemon=True
        ).start()

    def _do_send(self, recipient, country, amount, to_currency):
        rate, source = get_rate(BASE_CURRENCY, to_currency)
        base_equivalent = amount / rate
        fee = base_equivalent * (FEE_PERCENT / 100)
        total = base_equivalent + fee

        error = None
        new_balance = None

        try:
            conn = sqlite3.connect("bank.db")
            cursor = conn.cursor()

            sender_id = session.current_user[0]

            cursor.execute("SELECT balance FROM users WHERE id=?", (sender_id,))
            row = cursor.fetchone()

            if row is None:
                error = "Sender account not found."
            else:
                sender_balance = row[0]

                if sender_balance < total:
                    error = f"Insufficient balance. This transfer needs ₹{total:,.2f} including fees."
                else:
                    cursor.execute(
                        "UPDATE users SET balance = balance - ? WHERE id=?",
                        (total, sender_id)
                    )

                    cursor.execute(
                        """
                        INSERT INTO transactions
                        (user_id, transaction_type, receiver, amount)
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            sender_id,
                            "International Transfer",
                            f"{recipient} ({country})",
                            total
                        )
                    )

                    conn.commit()
                    new_balance = sender_balance - total

            conn.close()

        except sqlite3.Error as e:
            error = f"Database error: {e}"

        self.after(0, lambda: self._finish_send(error, new_balance, recipient, amount, to_currency, total))

    def _finish_send(self, error, new_balance, recipient, amount, to_currency, total):
        self.send_button.configure(state="normal", text="Send Internationally")

        if error:
            messagebox.showerror("Error", error)
            return

        # Preserve the full session tuple, including email at index 5 —
        # (id, name, username, password, balance, email)
       # Preserve the full session tuple regardless of its current length —
        # (id, name, username, password, balance, email); balance is index 4.
        current = list(session.current_user)
        current[4] = new_balance
        session.current_user = tuple(current)

        messagebox.showinfo(
            "Success",
            f"Sent {amount:,.2f} {to_currency} to {recipient}.\n"
            f"₹{total:,.2f} deducted (including {FEE_PERCENT}% fee)."
        )

        self.recipient_entry.delete(0, "end")
        self.amount_entry.delete(0, "end")

        app_layout = getattr(self, "master", None)
        app_layout = getattr(app_layout, "master", None)
        if app_layout is not None and hasattr(app_layout, "show_dashboard"):
            app_layout.show_dashboard()