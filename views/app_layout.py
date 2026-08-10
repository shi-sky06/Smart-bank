import customtkinter as ctk

from views.dashboard import DashboardPage
from views.deposit import DepositPage
from views.withdraw import WithdrawPage
from views.transfer import TransferPage
from views.transactions import TransactionsPage
from views.loan import LoanPage
from views.chatbot import ChatbotPage
from views.wrapped import WrappedPage

from assets.icon_loader import get_icon
from assets.ui_helpers import PAGE_COLORS


COLOR_SIDEBAR_BG = "#FFFFFF"
COLOR_SIDEBAR_BORDER = "#E5E8EC"
COLOR_NAV_DEFAULT = "#F3F4F6"
COLOR_NAV_DEFAULT_HOVER = "#E5E7EB"
COLOR_NAV_TEXT = "#374151"
COLOR_NAV_ACTIVE = "#1E3A8A"
COLOR_NAV_ACTIVE_HOVER = "#152C69"


class AppLayout(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.pack(fill="both", expand=True)

        # ==========================
        # Main Layout (responsive)
        # ==========================
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)   # Sidebar (fixed width)
        self.grid_columnconfigure(1, weight=1)   # Content (expands with window)

        # ==========================
        # Sidebar — white with blue accents
        # ==========================
        self.sidebar = ctk.CTkFrame(
            self,
            width=230,
            corner_radius=0,
            fg_color=COLOR_SIDEBAR_BG,
            border_width=0
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)

        # thin right border to separate sidebar from content
        divider = ctk.CTkFrame(self.sidebar, width=1, fg_color=COLOR_SIDEBAR_BORDER)
        divider.place(relx=1.0, rely=0, relheight=1.0, anchor="ne")

        # ==========================
        # Content Area (fills remaining space, scales with window)
        # ==========================
        self.content = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color="#F9FAFB"
        )
        self.content.grid(row=0, column=1, sticky="nsew")

        self.content.grid_rowconfigure(1, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        # ==========================
        # Header
        # ==========================
        self.header = ctk.CTkFrame(
            self.content,
            height=70,
            corner_radius=0,
            fg_color=COLOR_SIDEBAR_BG
        )
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

        self.back_button = ctk.CTkButton(
            self.header,
            text="⬅ Back",
            width=90,
            fg_color="transparent",
            border_width=1,
            border_color=COLOR_SIDEBAR_BORDER,
            text_color=COLOR_NAV_TEXT,
            hover_color=COLOR_NAV_DEFAULT,
            command=self.go_back
        )
        self.back_button.pack(side="left", padx=(20, 10))
        self.back_button.configure(state="disabled")

        logo_icon = get_icon("bank_logo", size=28)
        if logo_icon:
            ctk.CTkLabel(self.header, image=logo_icon, text="").pack(side="left", padx=(10, 8))

        ctk.CTkLabel(
            self.header,
            text="SmartBank AI",
            font=("Arial", 24, "bold"),
            text_color="#111827"
        ).pack(side="left")

        # ==========================
        # Sidebar Brand
        # ==========================
        brand_row = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_row.pack(pady=(30, 35))

        brand_icon = get_icon("bank_logo", size=44)
        if brand_icon:
            ctk.CTkLabel(brand_row, image=brand_icon, text="").pack()

        ctk.CTkLabel(
            brand_row,
            text="SmartBank",
            font=("Arial", 22, "bold"),
            text_color="#111827"
        ).pack(pady=(8, 0))

        # ==========================
        # Navigation Buttons (icon + text, active-state highlight)
        # ==========================
        self.nav_buttons = {}

        nav_items = [
            ("dashboard", "Dashboard", "house", self.show_dashboard),
            ("deposit", "Deposit", "money_bag", self.show_deposit),
            ("withdraw", "Withdraw", "down_arrow", self.show_withdraw),
            ("transfer", "Transfer", "repeat", self.show_transfer),
            ("transactions", "Transactions", "scroll", self.show_transactions),
            ("loan", "Loans", "credit_card", self.show_loans),
            ("chatbot", "AI Assistant", "robot", self.show_chatbot),
        ]

        for key, label, icon_name, command in nav_items:
            icon_img = get_icon(icon_name, size=18)

            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {label}",
                image=icon_img,
                compound="left",
                anchor="w",
                width=195,
                height=42,
                corner_radius=10,
                fg_color=COLOR_NAV_DEFAULT,
                hover_color=COLOR_NAV_DEFAULT_HOVER,
                text_color=COLOR_NAV_TEXT,
                font=("Arial", 14),
                command=command
            )
            btn.pack(pady=5, padx=18)
            self.nav_buttons[key] = btn

        # Push logout button to bottom
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        ctk.CTkButton(
            self.sidebar,
            text="🚪  Logout",
            width=195,
            height=42,
            corner_radius=10,
            fg_color="#FEF2F2",
            text_color="#DC2626",
            hover_color="#FEE2E2",
            font=("Arial", 14),
            command=self.logout
        ).pack(side="bottom", pady=20, padx=18)

        # ==========================
        # Navigation history (for Back button)
        # ==========================
        self.history = []
        self.current_page_class = None
        self.current_page_key = None

        # Show dashboard initially
        self.show_dashboard(add_to_history=False)

    # ==========================
    # Helper
    # ==========================

    def clear_page(self):
        if hasattr(self, "page"):
            self.page.destroy()

    def _set_active_nav(self, key):
        for nav_key, btn in self.nav_buttons.items():
            if nav_key == key:
                btn.configure(fg_color=COLOR_NAV_ACTIVE, hover_color=COLOR_NAV_ACTIVE_HOVER, text_color="white")
            else:
                btn.configure(fg_color=COLOR_NAV_DEFAULT, hover_color=COLOR_NAV_DEFAULT_HOVER, text_color=COLOR_NAV_TEXT)

    def load_page(self, page_class, add_to_history=True, nav_key=None):
        if add_to_history and self.current_page_class is not None:
            self.history.append(self.current_page_class)

        self.clear_page()

        self.page = page_class(self.content)

        self.page.grid(row=1, column=0, sticky="nsew")

        self.current_page_class = page_class
        self.current_page_key = nav_key

        if nav_key:
            self._set_active_nav(nav_key)

        self.back_button.configure(
            state="normal" if self.history else "disabled"
        )

    def go_back(self):
        if not self.history:
            return

        previous_page = self.history.pop()

        key_lookup = {
            DashboardPage: "dashboard",
            DepositPage: "deposit",
            WithdrawPage: "withdraw",
            TransferPage: "transfer",
            TransactionsPage: "transactions",
            LoanPage: "loan",
            ChatbotPage: "chatbot",
        }

        self.load_page(previous_page, add_to_history=False, nav_key=key_lookup.get(previous_page))

        self.back_button.configure(
            state="normal" if self.history else "disabled"
        )

    # ==========================
    # Navigation
    # ==========================

    def show_dashboard(self, add_to_history=True):
        self.load_page(DashboardPage, add_to_history=add_to_history, nav_key="dashboard")

    def show_deposit(self, add_to_history=True):
        self.load_page(DepositPage, add_to_history=add_to_history, nav_key="deposit")

    def show_withdraw(self, add_to_history=True):
        self.load_page(WithdrawPage, add_to_history=add_to_history, nav_key="withdraw")

    def show_transfer(self, add_to_history=True):
        self.load_page(TransferPage, add_to_history=add_to_history, nav_key="transfer")

    def show_transactions(self, add_to_history=True):
        self.load_page(TransactionsPage, add_to_history=add_to_history, nav_key="transactions")

    def show_loans(self, add_to_history=True):
        self.load_page(LoanPage, add_to_history=add_to_history, nav_key="loan")

    def show_chatbot(self, add_to_history=True):
        self.load_page(ChatbotPage, add_to_history=add_to_history, nav_key="chatbot")

    def show_wrapped(self, add_to_history=True):
        # Wrapped is a full-screen "story" experience — don't highlight
        # any sidebar nav item while it's open.
        self.load_page(WrappedPage, add_to_history=add_to_history, nav_key=None)

    # ==========================
    # Logout
    # ==========================

    def logout(self):
        import session

        session.current_user = None

        self.destroy()

        self.master.show_login()