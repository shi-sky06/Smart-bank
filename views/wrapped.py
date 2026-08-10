"""
views/wrapped.py

"SmartBank Wrapped" — a Spotify-Wrapped-style animated recap of the
user's banking activity, presented as a swipeable slideshow of
full-color cards.

All stats are computed live from the transactions/users tables —
no new schema needed.
"""

import customtkinter as ctk
import sqlite3
import session

from assets.icon_loader import get_icon


class WrappedPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="#0F172A")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.slides = self._build_slides()
        self.current_index = 0

        # Slide surface
        self.slide_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.slide_frame.grid(row=0, column=0, sticky="nsew", padx=40, pady=(30, 10))

        # Dots indicator
        self.dots_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dots_frame.grid(row=1, column=0, pady=(0, 10))
        self.dot_labels = []
        for i in range(len(self.slides)):
            dot = ctk.CTkLabel(self.dots_frame, text="●", font=("Arial", 14),
                                text_color="#374151")
            dot.pack(side="left", padx=4)
            self.dot_labels.append(dot)

        # Nav row
        nav_row = ctk.CTkFrame(self, fg_color="transparent")
        nav_row.grid(row=2, column=0, pady=(0, 30))

        self.back_btn = ctk.CTkButton(
            nav_row, text="← Previous", width=120,
            fg_color="transparent", border_width=1, border_color="#4B5563",
            text_color="#E5E7EB", hover_color="#1F2937",
            command=self.prev_slide
        )
        self.back_btn.pack(side="left", padx=10)

        self.close_btn = ctk.CTkButton(
            nav_row, text="✕ Close", width=100,
            fg_color="transparent", border_width=1, border_color="#4B5563",
            text_color="#E5E7EB", hover_color="#1F2937",
            command=self.close_wrapped
        )
        self.close_btn.pack(side="left", padx=10)

        self.next_btn = ctk.CTkButton(
            nav_row, text="Next →", width=120,
            fg_color="#7C3AED", hover_color="#6D28D9",
            command=self.next_slide
        )
        self.next_btn.pack(side="left", padx=10)

        self._render_slide()

    # =========================
    # Compute all stats up front
    # =========================
    def _build_slides(self):

        name = "there"
        try:
            name = session.current_user[1]
        except (TypeError, IndexError):
            pass

        user_id = None
        try:
            user_id = session.current_user[0]
        except (TypeError, IndexError):
            pass

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM transactions WHERE user_id=?", (user_id,))
        total_txns = cursor.fetchone()[0]

        cursor.execute(
            "SELECT IFNULL(SUM(amount),0) FROM transactions WHERE user_id=? AND transaction_type='Deposit'",
            (user_id,)
        )
        total_deposited = cursor.fetchone()[0]

        cursor.execute(
            "SELECT IFNULL(SUM(amount),0) FROM transactions WHERE user_id=? AND transaction_type='Withdraw'",
            (user_id,)
        )
        total_withdrawn = cursor.fetchone()[0]

        cursor.execute(
            "SELECT IFNULL(SUM(amount),0) FROM transactions WHERE user_id=? AND transaction_type='Transfer'",
            (user_id,)
        )
        total_transferred = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT transaction_type, amount FROM transactions
            WHERE user_id=? ORDER BY amount DESC LIMIT 1
            """,
            (user_id,)
        )
        biggest = cursor.fetchone()

        # Percentile among savers, by balance
        cursor.execute("SELECT balance FROM users ORDER BY balance ASC")
        all_balances = [r[0] for r in cursor.fetchall()]

        cursor.execute("SELECT balance FROM users WHERE id=?", (user_id,))
        row = cursor.fetchone()
        my_balance = row[0] if row else 0

        if all_balances:
            rank = sum(1 for b in all_balances if b <= my_balance)
            percentile = round((rank / len(all_balances)) * 100)
        else:
            percentile = 100

        conn.close()

        slides = []

        # Slide 1 — Intro
        slides.append({
            "bg": "#1E3A8A", "icon": "bank_logo", "icon_size": 64,
            "title": f"Hey {name} 👋",
            "subtitle": "Here's your SmartBank Wrapped",
            "big": "",
        })

        # Slide 2 — Total activity
        slides.append({
            "bg": "#2563EB", "icon": "scroll", "icon_size": 56,
            "title": "You made",
            "big": f"{total_txns}",
            "subtitle": "transactions with SmartBank",
        })

        # Slide 3 — Deposited
        slides.append({
            "bg": "#16A34A", "icon": "money_bag", "icon_size": 56,
            "title": "You deposited a total of",
            "big": f"₹{total_deposited:,.0f}",
            "subtitle": "Nice work building up your balance 💪",
        })

        # Slide 4 — Withdrawn
        slides.append({
            "bg": "#DC2626", "icon": "down_arrow", "icon_size": 56,
            "title": "You withdrew a total of",
            "big": f"₹{total_withdrawn:,.0f}",
            "subtitle": "Every rupee counts",
        })

        # Slide 5 — Transferred
        slides.append({
            "bg": "#0EA5E9", "icon": "repeat", "icon_size": 56,
            "title": "You sent",
            "big": f"₹{total_transferred:,.0f}",
            "subtitle": "in transfers to other SmartBank users",
        })

        # Slide 6 — Biggest transaction
        if biggest:
            b_type, b_amount = biggest
            slides.append({
                "bg": "#9333EA", "icon": "chart_up", "icon_size": 56,
                "title": "Your biggest single move",
                "big": f"₹{b_amount:,.0f}",
                "subtitle": f"A {b_type.lower()} — go big or go home",
            })

        # Slide 7 — Percentile finale
        slides.append({
            "bg": "#D97706", "icon": "bar_chart", "icon_size": 60,
            "title": "You're in the",
            "big": f"Top {100 - percentile}%",
            "subtitle": "of savers at SmartBank 🏆",
            "finale": True,
        })

        return slides

    # =========================
    # Render current slide
    # =========================
    def _render_slide(self):

        for widget in self.slide_frame.winfo_children():
            widget.destroy()

        slide = self.slides[self.current_index]

        self.configure(fg_color=slide["bg"])
        self.slide_frame.configure(fg_color="transparent")

        content = ctk.CTkFrame(self.slide_frame, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        icon_img = get_icon(slide["icon"], size=slide.get("icon_size", 56))
        if icon_img:
            ctk.CTkLabel(content, image=icon_img, text="").pack(pady=(0, 20))

        ctk.CTkLabel(
            content, text=slide["title"], font=("Arial", 22, "bold"),
            text_color="white"
        ).pack()

        if slide.get("big"):
            ctk.CTkLabel(
                content, text=slide["big"], font=("Arial", 52, "bold"),
                text_color="white"
            ).pack(pady=(10, 10))

        ctk.CTkLabel(
            content, text=slide.get("subtitle", ""), font=("Arial", 15),
            text_color="#E5E7EB", wraplength=500, justify="center"
        ).pack()

        if slide.get("finale"):
            ctk.CTkLabel(
                content, text="✨ 🎉 ✨", font=("Arial", 24)
            ).pack(pady=(20, 0))

        # Update dots
        for i, dot in enumerate(self.dot_labels):
            dot.configure(text_color="white" if i == self.current_index else "#6B7280")

        # Update nav button states
        self.back_btn.configure(state="disabled" if self.current_index == 0 else "normal")
        self.next_btn.configure(
            text="Finish ✓" if self.current_index == len(self.slides) - 1 else "Next →"
        )

    # =========================
    # Navigation
    # =========================
    def next_slide(self):
        if self.current_index < len(self.slides) - 1:
            self.current_index += 1
            self._render_slide()
        else:
            self.close_wrapped()

    def prev_slide(self):
        if self.current_index > 0:
            self.current_index -= 1
            self._render_slide()

    def close_wrapped(self):
        app_layout = getattr(self, "master", None)
        app_layout = getattr(app_layout, "master", None)
        if app_layout is not None and hasattr(app_layout, "show_dashboard"):
            app_layout.show_dashboard()