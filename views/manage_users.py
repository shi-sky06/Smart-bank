import customtkinter as ctk
import sqlite3
from tkinter import messagebox

from assets.ui_helpers import build_hero_header
from assets.icon_loader import get_icon

ADMIN_ACCENT = "#0F172A"


class ManageUsersPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.master = master
        self.selected_user_id = None

        self.configure(fg_color="#F9FAFB")

        build_hero_header(
            self,
            title="Manage Users",
            subtitle="View, search, and edit customer accounts",
            icon_name="bust",
            accent_color=ADMIN_ACCENT,
            icon_size=40,
            height=100
        )

        wrapper = ctk.CTkScrollableFrame(self, fg_color="transparent")
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

        # -------------------------
        # User List Card
        # -------------------------
        list_card = ctk.CTkFrame(wrapper, corner_radius=15, border_width=1, border_color="#E5E8EC")
        list_card.pack(fill="x", pady=(0, 20))

        ctk.CTkFrame(list_card, height=6, corner_radius=0, fg_color=ADMIN_ACCENT).pack(fill="x", side="top")

        # -------------------------
        # Search / Filter
        # -------------------------
        search_row = ctk.CTkFrame(list_card, fg_color="transparent")
        search_row.pack(fill="x", padx=15, pady=(15, 0))

        self.search_entry = ctk.CTkEntry(
            search_row,
            width=280,
            placeholder_text="🔍  Search by name, username, or email"
        )
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda e: self.filter_users())

        ctk.CTkButton(
            search_row,
            text="Clear",
            width=80,
            fg_color="transparent",
            border_width=1,
            border_color="#D1D5DB",
            text_color="#374151",
            hover_color="#F3F4F6",
            command=self.clear_search
        ).pack(side="left")

        self.user_list = ctk.CTkTextbox(
            list_card,
            width=800,
            height=200,
            font=("Arial", 13)
        )
        self.user_list.pack(padx=15, pady=15, fill="x")

        ctk.CTkButton(
            list_card,
            text="🔄  Refresh Users",
            fg_color=ADMIN_ACCENT,
            hover_color="#020617",
            command=self.load_users
        ).pack(pady=(0, 15))

        # -------------------------
        # Edit Card
        # -------------------------
        edit_card = ctk.CTkFrame(wrapper, corner_radius=15, border_width=1, border_color="#E5E8EC")
        edit_card.pack(fill="x")

        ctk.CTkFrame(edit_card, height=6, corner_radius=0, fg_color="#1E3A8A").pack(fill="x", side="top")

        ctk.CTkLabel(
            edit_card, text="Edit User", font=("Arial", 16, "bold"), text_color="#111827"
        ).pack(pady=(15, 10))

        self.id_entry = ctk.CTkEntry(
            edit_card,
            width=300,
            placeholder_text="🆔  Enter User ID"
        )
        self.id_entry.pack(pady=5)

        ctk.CTkButton(
            edit_card,
            text="Load User",
            fg_color="#1E3A8A",
            hover_color="#152C69",
            command=self.load_user
        ).pack(pady=8)

        self.name = ctk.CTkEntry(edit_card, width=350, placeholder_text="🧑  Name")
        self.name.pack(pady=5)

        self.username = ctk.CTkEntry(edit_card, width=350, placeholder_text="👤  Username")
        self.username.pack(pady=5)

        self.email = ctk.CTkEntry(edit_card, width=350, placeholder_text="✉️  Email")
        self.email.pack(pady=5)

        self.balance = ctk.CTkEntry(edit_card, width=350, placeholder_text="💰  Balance")
        self.balance.pack(pady=5)

        ctk.CTkButton(
            edit_card,
            text="💾  Save Changes",
            fg_color="#16A34A",
            hover_color="#15803D",
            command=self.save_changes
        ).pack(pady=(15, 20))

        self.load_users()

    # -------------------------
    # Load all users
    # -------------------------

    def load_users(self):

        self.user_list.delete("1.0", "end")

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT id,name,username,balance,email
        FROM users
        """)

        users = cursor.fetchall()

        conn.close()

        self._all_users = users
        self._render_users(users)

    # -------------------------
    # Render a list of users into the textbox
    # -------------------------

    def _render_users(self, users):

        self.user_list.delete("1.0", "end")

        if not users:
            self.user_list.insert("end", "No matching users found.")
            return

        for user in users:

            self.user_list.insert(
                "end",
                f"ID:{user[0]} | {user[1]} | {user[2]} | ₹{user[3]} | {user[4]}\n"
            )

    # -------------------------
    # Search / Filter (client-side, over the already-loaded list)
    # -------------------------

    def filter_users(self):

        query = self.search_entry.get().strip().lower()

        if not hasattr(self, "_all_users"):
            return

        if not query:
            self._render_users(self._all_users)
            return

        filtered = [
            u for u in self._all_users
            if query in str(u[1]).lower()      # name
            or query in str(u[2]).lower()      # username
            or query in str(u[4]).lower()      # email
        ]

        self._render_users(filtered)

    def clear_search(self):
        self.search_entry.delete(0, "end")
        if hasattr(self, "_all_users"):
            self._render_users(self._all_users)

    # -------------------------
    # Load selected user
    # -------------------------

    def load_user(self):

        user_id = self.id_entry.get()

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute("""
        SELECT *
        FROM users
        WHERE id=?
        """, (user_id,))

        user = cursor.fetchone()

        conn.close()

        if not user:
            messagebox.showerror("Error", "User not found")
            return

        self.selected_user_id = user[0]

        self.name.delete(0, "end")
        self.username.delete(0, "end")
        self.email.delete(0, "end")
        self.balance.delete(0, "end")

        self.name.insert(0, "" if user[1] is None else str(user[1]))
        self.username.insert(0, "" if user[2] is None else str(user[2]))
        self.email.insert(0, "" if user[3] is None else str(user[3]))
        self.balance.insert(0, "" if user[5] is None else str(user[5]))
        # Note: user[4] is the password hash — intentionally never shown/edited here.

    # -------------------------
    # Save Changes
    # -------------------------

    def save_changes(self):

        if self.selected_user_id is None:
            messagebox.showerror("Error", "Load a user first")
            return

        balance_text = self.balance.get().strip()

        try:
            balance_value = float(balance_text)
        except ValueError:
            messagebox.showerror(
                "Error",
                f"Balance must be a number. Got: \"{balance_text}\"\n\n"
                "If this looks like an email or other text, this account's "
                "data may be corrupted — check repair_users.py."
            )
            return

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute("""
        UPDATE users
        SET
            name=?,
            username=?,
            balance=?,
            email=?
        WHERE id=?
        """,
        (
            self.name.get(),
            self.username.get(),
            balance_value,
            self.email.get(),
            self.selected_user_id
        ))

        conn.commit()
        conn.close()

        messagebox.showinfo(
            "Success",
            "User updated successfully."
        )

        self.load_users()

    # -------------------------
    # Back to Admin Dashboard
    # -------------------------

    def go_back(self):
        self.master.show_admin_dashboard()