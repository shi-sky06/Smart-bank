import customtkinter as ctk
from tkinter import messagebox
import time
import database
import session

from views.login import LoginPage
from views.register import RegisterPage
from views.app_layout import AppLayout
from views.admin_login import AdminLoginPage
from views.admin_dashboard import AdminDashboardPage

# ==========================
# CustomTkinter Settings
# ==========================
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# ==========================
# Inactivity auto-logout
# ==========================
INACTIVITY_LIMIT_SECONDS = 5 * 60  # 5 minutes — adjust as needed
INACTIVITY_CHECK_INTERVAL_MS = 15000  # check every 15 seconds


class SmartBank(ctk.CTk):

    def __init__(self):
        super().__init__()

        # Create database
        database.create_database()

        # Window
        self.title("🏦 SmartBank AI")

        try:
            self.state("zoomed")
        except:
            self.attributes("-zoomed", True)

        self.minsize(1000, 650)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.current_page = None

        # ==========================
        # Inactivity tracking
        # ==========================
        self.is_logged_in = False
        self.last_activity_time = time.time()

        self.bind_all("<Motion>", self._register_activity)
        self.bind_all("<KeyPress>", self._register_activity)
        self.bind_all("<Button>", self._register_activity)

        self._check_inactivity()

        # Open Login Page
        self.show_login()

    # ==========================
    # Inactivity handling
    # ==========================
    def _register_activity(self, event=None):
        self.last_activity_time = time.time()

    def _check_inactivity(self):
        if self.is_logged_in:
            elapsed = time.time() - self.last_activity_time
            if elapsed > INACTIVITY_LIMIT_SECONDS:
                self.is_logged_in = False
                session.current_user = None

                messagebox.showwarning(
                    "Session Expired",
                    "You've been logged out due to inactivity."
                )

                self.show_login()

        self.after(INACTIVITY_CHECK_INTERVAL_MS, self._check_inactivity)

    # ==========================
    # Remove Current Page
    # ==========================
    def clear_page(self):
        if self.current_page is not None:
            self.current_page.destroy()
            self.current_page = None

    # ==========================
    # Customer Login
    # ==========================
    def show_login(self):
        self.is_logged_in = False
        self.clear_page()

        self.current_page = LoginPage(self)
        self.current_page.pack(fill="both", expand=True)

    # ==========================
    # Register
    # ==========================
    def show_register(self):
        self.is_logged_in = False
        self.clear_page()

        self.current_page = RegisterPage(self)
        self.current_page.pack(fill="both", expand=True)

    # ==========================
    # Customer Dashboard
    # ==========================
    def show_app(self):
        self.is_logged_in = True
        self.last_activity_time = time.time()
        self.clear_page()

        self.current_page = AppLayout(self)
        self.current_page.pack(fill="both", expand=True)

    # ==========================
    # Admin Login
    # ==========================
    def show_admin_login(self):
        self.is_logged_in = False
        self.clear_page()

        self.current_page = AdminLoginPage(self)
        self.current_page.pack(fill="both", expand=True)

    # ==========================
    # Admin Dashboard
    # ==========================
    def show_admin_dashboard(self):
        self.is_logged_in = True
        self.last_activity_time = time.time()
        self.clear_page()

        self.current_page = AdminDashboardPage(self)
        self.current_page.pack(fill="both", expand=True)

    # ==========================
    # Manage Users
    # ==========================
    def show_manage_users(self):
        self.clear_page()

        from views.manage_users import ManageUsersPage

        self.current_page = ManageUsersPage(self)
        self.current_page.pack(fill="both", expand=True)

    # ==========================
    # Show Admin Transactions
    # ==========================
    def show_admin_transactions(self):
        self.clear_page()

        from views.admin_transactions import AdminTransactionsPage

        self.current_page = AdminTransactionsPage(self)
        self.current_page.pack(fill="both", expand=True)

    # ==========================
    # Bank Statistics
    # ==========================
    def show_bank_statistics(self):
        self.clear_page()

        from views.bank_statistics import BankStatisticsPage

        self.current_page = BankStatisticsPage(self)
        self.current_page.pack(fill="both", expand=True)

    # ==========================
    # Loan Verification
    # ==========================
    def show_loan_verification(self):
        self.clear_page()

        from views.loan_verification import LoanVerificationPage

        self.current_page = LoanVerificationPage(self)
        self.current_page.pack(fill="both", expand=True)

    # ==========================
    # Document Verification
    # ==========================
    def show_document_verification(self):
        self.clear_page()

        from views.document_verification import DocumentVerificationPage

        self.current_page = DocumentVerificationPage(self)
        self.current_page.pack(fill="both", expand=True)


# ==========================
# Run Application
# ==========================
if __name__ == "__main__":
    app = SmartBank()
    app.mainloop()
    
