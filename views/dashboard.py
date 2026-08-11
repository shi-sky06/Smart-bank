import customtkinter as ctk
import sqlite3
import session

from assets.icon_loader import get_icon
from achievements import get_user_achievements


# =========================
# Color Palette
# =========================
COLOR_BORDER = "#E5E8EC"

COLOR_BALANCE_ACCENT = "#16A34A"   # green
COLOR_BALANCE_BG = "#DCFCE7"
COLOR_BALANCE_HOVER_BG = "#F0FDF4"

COLOR_TXN_ACCENT = "#2563EB"       # blue
COLOR_TXN_BG = "#DBEAFE"
COLOR_TXN_HOVER_BG = "#EFF6FF"

COLOR_AI_ACCENT = "#9333EA"        # purple
COLOR_AI_BG = "#F3E8FF"
COLOR_AI_HOVER_BG = "#FAF5FF"

COLOR_CARD_BG = "#FFFFFF"

COLOR_TEXT_MUTED = "#6B7280"
COLOR_TEXT_DARK = "#111827"

COLOR_DEPOSIT = "#16A34A"
COLOR_WITHDRAW = "#DC2626"
COLOR_TRANSFER = "#2563EB"
COLOR_DEFAULT_TXN = "#374151"

# Hero banner colors (bank-style gradient look using two stacked frames)
COLOR_HERO_BG = "#1E3A8A"   # deep banking blue
COLOR_HERO_BG_LIGHT = "#2563EB"


class DashboardPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="transparent")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # =========================
        # Fetch User Data (error-safe)
        # =========================
        user = None
        transactions = []
        fetch_error = None

        try:
            conn = sqlite3.connect("bank.db")
            cursor = conn.cursor()

            user_id = session.current_user[0]

            cursor.execute("""
                SELECT id, name, username, balance
                FROM users
                WHERE id=?
            """, (user_id,))

            user = cursor.fetchone()

            if user is not None:
                cursor.execute("""
                    SELECT transaction_type, amount
                    FROM transactions
                    WHERE user_id=?
                    ORDER BY date DESC
                    LIMIT 5
                """, (user[0],))

                transactions = cursor.fetchall()

            conn.close()

        except (TypeError, IndexError):
            # session.current_user missing or malformed
            fetch_error = "You're not logged in. Please log in again."

        except sqlite3.Error as e:
            fetch_error = f"Could not load your dashboard right now.\n\nDatabase error: {e}"

        if user is None and fetch_error is None:
            fetch_error = "We couldn't find your account. Please log in again."

        if fetch_error:
            self._build_error_state(fetch_error)
            return

        user_id = user[0]
        name = user[1]
        balance = user[3]

        # =========================
        # Layout
        # =========================
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        # =========================
        # Hero Banner
        # =========================
        hero = ctk.CTkFrame(
            container,
            corner_radius=18,
            fg_color=COLOR_HERO_BG,
            height=140
        )
        hero.pack(fill="x", pady=(0, 25))
        hero.pack_propagate(False)

        hero_content = ctk.CTkFrame(hero, fg_color="transparent")
        hero_content.pack(expand=True, fill="both", padx=30, pady=20)
        hero_content.grid_columnconfigure(1, weight=1)

        bank_icon = get_icon("bank_logo", size=56)
        if bank_icon:
            ctk.CTkLabel(hero_content, image=bank_icon, text="").grid(
                row=0, column=0, rowspan=2, padx=(0, 20)
            )
        else:
            ctk.CTkLabel(hero_content, text="🏦", font=("Arial", 44)).grid(
                row=0, column=0, rowspan=2, padx=(0, 20)
            )

        ctk.CTkLabel(
            hero_content,
            text="SmartBank AI Dashboard",
            font=("Arial", 26, "bold"),
            text_color="white"
        ).grid(row=0, column=1, sticky="w")

        wave_icon = get_icon("wave", size=20)
        welcome_row = ctk.CTkFrame(hero_content, fg_color="transparent")
        welcome_row.grid(row=1, column=1, sticky="w", pady=(4, 0))

        ctk.CTkLabel(
            welcome_row,
            text=f"Welcome back, {name}",
            font=("Arial", 15),
            text_color="#DBEAFE"
        ).pack(side="left")

        if wave_icon:
            ctk.CTkLabel(welcome_row, image=wave_icon, text="").pack(side="left", padx=(8, 0))

        # =========================
        # Stat Cards (clickable)
        # =========================
        cards = ctk.CTkFrame(container, fg_color="transparent")
        cards.pack(fill="x", pady=10)
        cards.grid_columnconfigure((0, 1, 2), weight=1, uniform="cards")

        self._build_stat_card(
            cards, column=0,
            icon_name="money_bag", label="Balance",
            value=f"₹ {balance:,.2f}",
            accent=COLOR_BALANCE_ACCENT,
            accent_bg=COLOR_BALANCE_BG,
            hover_bg=COLOR_BALANCE_HOVER_BG,
            hint="Tap to deposit →",
            on_click=self._go_deposit
        )

        self._build_stat_card(
            cards, column=1,
            icon_name="scroll", label="Transactions",
            value=f"{len(transactions)} Recent",
            accent=COLOR_TXN_ACCENT,
            accent_bg=COLOR_TXN_BG,
            hover_bg=COLOR_TXN_HOVER_BG,
            hint="Tap to view all →",
            on_click=self._go_transactions
        )

        self._build_stat_card(
            cards, column=2,
            icon_name="robot", label="Milo AI",
            value="ONLINE", value_dot=True,
            accent=COLOR_AI_ACCENT,
            accent_bg=COLOR_AI_BG,
            hover_bg=COLOR_AI_HOVER_BG,
            hint="Tap to chat →",
            on_click=self._go_chatbot
        )

        # =========================
        # Account Details
        # =========================
        details = ctk.CTkFrame(
            container,
            corner_radius=15,
            fg_color=COLOR_CARD_BG,
            border_width=1,
            border_color=COLOR_BORDER
        )
        details.pack(fill="x", pady=(20, 10))
        details.grid_columnconfigure((0, 1), weight=1, uniform="details")

        self._build_detail_item(details, column=0, icon_name="bust", label="ACCOUNT HOLDER", value=name)
        self._build_detail_item(details, column=1, icon_name="id_button", label="ACCOUNT ID", value=str(user_id))

        # =========================
        # Wrapped Callout
        # =========================
        wrapped_card = ctk.CTkFrame(container, corner_radius=15, fg_color="#7C3AED", cursor="hand2")
        wrapped_card.pack(fill="x", pady=(20, 10))

        wrapped_inner = ctk.CTkFrame(wrapped_card, fg_color="transparent")
        wrapped_inner.pack(fill="x", padx=25, pady=18)

        ctk.CTkLabel(
            wrapped_inner, text="✨", font=("Arial", 26)
        ).pack(side="left", padx=(0, 15))

        text_col = ctk.CTkFrame(wrapped_inner, fg_color="transparent")
        text_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            text_col, text="Your SmartBank Wrapped is ready", font=("Arial", 16, "bold"),
            text_color="white", anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            text_col, text="See your year in banking, story-style", font=("Arial", 12),
            text_color="#EDE9FE", anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            wrapped_inner, text="View →", font=("Arial", 13, "bold"), text_color="white"
        ).pack(side="right")

        def open_wrapped(event=None):
            app_layout = getattr(self, "master", None)
            app_layout = getattr(app_layout, "master", None)
            if app_layout is not None and hasattr(app_layout, "show_wrapped"):
                app_layout.show_wrapped()

        for widget in [wrapped_card, wrapped_inner, text_col] + wrapped_inner.winfo_children() + text_col.winfo_children():
            widget.bind("<Button-1>", open_wrapped)
            widget.configure(cursor="hand2") if hasattr(widget, "configure") else None

        # =========================
        # Achievements
        # =========================
        achievements_card = ctk.CTkFrame(
            container, corner_radius=15, fg_color=COLOR_CARD_BG,
            border_width=1, border_color=COLOR_BORDER
        )
        achievements_card.pack(fill="x", pady=10)

        ach_header = ctk.CTkFrame(achievements_card, fg_color="transparent")
        ach_header.pack(anchor="w", padx=20, pady=(18, 5))

        ctk.CTkLabel(
            ach_header, text="🏆 Achievements", font=("Arial", 18, "bold"),
            text_color=COLOR_TEXT_DARK
        ).pack(side="left")

        try:
            badges = get_user_achievements(user_id)
        except Exception:
            badges = []

        unlocked_count = sum(1 for b in badges if b["unlocked"])

        ctk.CTkLabel(
            ach_header, text=f"  {unlocked_count}/{len(badges)} unlocked",
            font=("Arial", 12), text_color=COLOR_TEXT_MUTED
        ).pack(side="left", padx=(8, 0))

        badges_grid = ctk.CTkFrame(achievements_card, fg_color="transparent")
        badges_grid.pack(fill="x", padx=15, pady=(5, 20))

        for i in range(3):
            badges_grid.grid_columnconfigure(i, weight=1, uniform="badges")

        for i, badge in enumerate(badges):
            self._build_badge(badges_grid, badge, row=i // 3, column=i % 3)

        # =========================
        # Recent Activity
        # =========================
        recent = ctk.CTkFrame(
            container,
            corner_radius=15,
            fg_color=COLOR_CARD_BG,
            border_width=1,
            border_color=COLOR_BORDER
        )
        recent.pack(fill="both", expand=True, pady=10)

        header_row = ctk.CTkFrame(recent, fg_color="transparent")
        header_row.pack(anchor="w", padx=20, pady=(18, 10))

        chart_icon = get_icon("bar_chart", size=22)
        if chart_icon:
            ctk.CTkLabel(header_row, image=chart_icon, text="").pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            header_row,
            text="Recent Activity",
            font=("Arial", 20, "bold"),
            text_color=COLOR_TEXT_DARK
        ).pack(side="left")

        transaction_box = ctk.CTkScrollableFrame(
            recent, height=220, fg_color="transparent"
        )
        transaction_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        if transactions:
            for i, t in enumerate(transactions):
                self._build_transaction_row(transaction_box, t, i)
        else:
            ctk.CTkLabel(
                transaction_box,
                text="No transactions yet.",
                font=("Arial", 15),
                text_color=COLOR_TEXT_MUTED
            ).pack(pady=20)

    # =========================
    # Error state (replaces the whole page body on failure)
    # =========================
    def _build_error_state(self, message):
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_rowconfigure(0, weight=1)
        wrapper.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            wrapper,
            corner_radius=15,
            fg_color=COLOR_CARD_BG,
            border_width=1,
            border_color=COLOR_BORDER
        )
        card.grid(row=0, column=0)

        ctk.CTkLabel(
            card, text="⚠️", font=("Arial", 36)
        ).pack(pady=(30, 10), padx=50)

        ctk.CTkLabel(
            card, text="Something went wrong", font=("Arial", 18, "bold"),
            text_color=COLOR_TEXT_DARK
        ).pack(padx=50)

        ctk.CTkLabel(
            card, text=message, font=("Arial", 13), text_color=COLOR_TEXT_MUTED,
            wraplength=350, justify="center"
        ).pack(pady=(8, 25), padx=50)

        ctk.CTkButton(
            card, text="Back to Login", width=200,
            fg_color=COLOR_HERO_BG, hover_color="#152C69",
            command=self._go_login
        ).pack(pady=(0, 30))

    def _go_login(self):
        app = self.winfo_toplevel()
        if hasattr(app, "show_login"):
            app.show_login()

    # =========================
    # Helper: Achievement Badge
    # =========================
    def _build_badge(self, parent, badge, row, column):

        unlocked = badge["unlocked"]

        bg_color = badge["bg"] if unlocked else "#F3F4F6"
        icon_color_bg = badge["bg"] if unlocked else "#E5E7EB"
        text_color = COLOR_TEXT_DARK if unlocked else "#9CA3AF"
        title_color = badge["color"] if unlocked else "#9CA3AF"

        card = ctk.CTkFrame(parent, corner_radius=12, fg_color=bg_color)
        card.grid(row=row, column=column, padx=8, pady=8, sticky="nsew")

        badge_icon = ctk.CTkFrame(
            card, width=44, height=44, corner_radius=22, fg_color=icon_color_bg
        )
        badge_icon.pack(pady=(16, 8))
        badge_icon.pack_propagate(False)

        icon_img = get_icon(badge["icon"], size=20)
        if icon_img:
            ctk.CTkLabel(badge_icon, image=icon_img, text="").place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card, text=badge["label"], font=("Arial", 13, "bold"), text_color=title_color
        ).pack(padx=10)

        ctk.CTkLabel(
            card, text=badge["description"] if unlocked else "🔒 Locked",
            font=("Arial", 10), text_color=text_color, wraplength=140, justify="center"
        ).pack(padx=10, pady=(2, 16))

    # =========================
    # Navigation helpers
    # =========================
    def _app_layout(self):
        app_layout = getattr(self, "master", None)
        app_layout = getattr(app_layout, "master", None)
        return app_layout

    def _go_deposit(self):
        app_layout = self._app_layout()
        if app_layout is not None and hasattr(app_layout, "show_deposit"):
            app_layout.show_deposit()

    def _go_transactions(self):
        app_layout = self._app_layout()
        if app_layout is not None and hasattr(app_layout, "show_transactions"):
            app_layout.show_transactions()

    def _go_chatbot(self):
        app_layout = self._app_layout()
        if app_layout is not None and hasattr(app_layout, "show_chatbot"):
            app_layout.show_chatbot()

    # =========================
    # Helper: bind click + hover recursively
    # =========================
    def _make_interactive(self, root_widget, on_click, enter_cb, leave_cb):
        def bind_widget(widget):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", lambda e=None: on_click())
            widget.bind("<Enter>", lambda e=None: enter_cb())
            widget.bind("<Leave>", lambda e=None: leave_cb())
            for child in widget.winfo_children():
                bind_widget(child)

        bind_widget(root_widget)

    # =========================
    # Helper: Stat Card (clickable, hoverable, with icon image)
    # =========================
    def _build_stat_card(self, parent, column, icon_name, label, value,
                          accent, accent_bg, hover_bg, hint, on_click,
                          value_dot=False):

        card = ctk.CTkFrame(
            parent,
            corner_radius=15,
            fg_color=COLOR_CARD_BG,
            border_width=2,
            border_color=COLOR_BORDER
        )
        card.grid(row=0, column=column, sticky="nsew", padx=10)

        stripe = ctk.CTkFrame(card, height=6, corner_radius=0, fg_color=accent)
        stripe.pack(fill="x", side="top")

        badge = ctk.CTkFrame(
            card, width=56, height=56, corner_radius=28, fg_color=accent_bg
        )
        badge.pack(pady=(20, 10))
        badge.pack_propagate(False)

        icon_img = get_icon(icon_name, size=28)
        if icon_img:
            ctk.CTkLabel(badge, image=icon_img, text="").place(relx=0.5, rely=0.5, anchor="center")
        else:
            ctk.CTkLabel(badge, text="•", font=("Arial", 22)).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            card,
            text=label.upper(),
            font=("Arial", 12, "bold"),
            text_color=COLOR_TEXT_MUTED
        ).pack(pady=(0, 4))

        if value_dot:
            value_row = ctk.CTkFrame(card, fg_color="transparent")
            value_row.pack(pady=(0, 6))

            ctk.CTkLabel(
                value_row,
                text=value,
                font=("Arial", 20, "bold"),
                text_color=accent
            ).pack(side="left")

            dot_img = get_icon("green_dot", size=12)
            if dot_img:
                ctk.CTkLabel(value_row, image=dot_img, text="").pack(side="left", padx=(6, 0))
            else:
                dot = ctk.CTkFrame(value_row, width=10, height=10, corner_radius=5, fg_color=accent)
                dot.pack(side="left", padx=(8, 0), pady=(4, 0))
        else:
            ctk.CTkLabel(
                card,
                text=value,
                font=("Arial", 22, "bold"),
                text_color=COLOR_TEXT_DARK
            ).pack(pady=(0, 6))

        hint_label = ctk.CTkLabel(
            card,
            text=hint,
            font=("Arial", 11, "bold"),
            text_color=accent
        )
        hint_label.pack(pady=(0, 18))

        def on_enter():
            card.configure(fg_color=hover_bg, border_color=accent)

        def on_leave():
            card.configure(fg_color=COLOR_CARD_BG, border_color=COLOR_BORDER)

        self._make_interactive(card, on_click, on_enter, on_leave)

    # =========================
    # Helper: Account Detail Item (with icon image)
    # =========================
    def _build_detail_item(self, parent, column, icon_name, label, value):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=0, column=column, sticky="w", padx=25, pady=18)

        label_row = ctk.CTkFrame(wrap, fg_color="transparent")
        label_row.pack(anchor="w")

        icon_img = get_icon(icon_name, size=16)
        if icon_img:
            ctk.CTkLabel(label_row, image=icon_img, text="").pack(side="left", padx=(0, 6))

        ctk.CTkLabel(
            label_row,
            text=label,
            font=("Arial", 12, "bold"),
            text_color=COLOR_TEXT_MUTED
        ).pack(side="left")

        ctk.CTkLabel(
            wrap,
            text=value,
            font=("Arial", 17, "bold"),
            text_color=COLOR_TEXT_DARK
        ).pack(anchor="w", pady=(2, 0))

    # =========================
    # Helper: Transaction Row (with icon image)
    # =========================
    def _build_transaction_row(self, parent, transaction, index):
        txn_type, amount = transaction
        txn_type_clean = str(txn_type).strip().lower()

        if "deposit" in txn_type_clean:
            color = COLOR_DEPOSIT
            bg = "#F0FDF4"
            icon_name = "up_arrow"
            sign = "+"
        elif "withdraw" in txn_type_clean:
            color = COLOR_WITHDRAW
            bg = "#FEF2F2"
            icon_name = "down_arrow"
            sign = "-"
        elif "transfer" in txn_type_clean:
            color = COLOR_TRANSFER
            bg = "#EFF6FF"
            icon_name = "repeat"
            sign = "-"
        else:
            color = COLOR_DEFAULT_TXN
            bg = "#F9FAFB"
            icon_name = None
            sign = ""

        row = ctk.CTkFrame(parent, fg_color=bg, corner_radius=10)
        row.pack(fill="x", padx=5, pady=4)
        row.grid_columnconfigure(1, weight=1)

        icon_img = get_icon(icon_name, size=18) if icon_name else None
        if icon_img:
            ctk.CTkLabel(row, image=icon_img, text="", width=30).grid(row=0, column=0, padx=(10, 5), pady=10)
        else:
            ctk.CTkLabel(row, text="•", font=("Arial", 16), text_color=color, width=30).grid(
                row=0, column=0, padx=(10, 5), pady=10
            )

        ctk.CTkLabel(
            row,
            text=str(txn_type).title(),
            font=("Arial", 14, "bold"),
            text_color=COLOR_TEXT_DARK,
            anchor="w"
        ).grid(row=0, column=1, sticky="w", pady=10)

        ctk.CTkLabel(
            row,
            text=f"{sign} ₹ {amount:,.2f}",
            font=("Arial", 14, "bold"),
            text_color=color
        ).grid(row=0, column=2, padx=(5, 15), pady=10)