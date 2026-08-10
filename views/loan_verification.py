import customtkinter as ctk
from tkinter import ttk, messagebox
import sqlite3

from assets.ui_helpers import build_hero_header

VERIFY_ACCENT = "#9333EA"


class LoanVerificationPage(ctk.CTkFrame):
    """
    Loans are auto-approved/rejected by credit score at the moment the
    customer applies (see LoanPage.apply_loan). This page is an admin
    OVERSIGHT tool: review every loan's auto-decision and manually
    override status if needed. It does NOT credit/debit any balance —
    it only updates the `loans.status` column.
    """

    def __init__(self, master):
        super().__init__(master)

        self.master = master
        self.selected_loan_id = None

        self.configure(fg_color="#F9FAFB")
        self.pack(fill="both", expand=True)

        build_hero_header(
            self,
            title="Loan Verification",
            subtitle="Review auto-decisions and override loan status",
            icon_name="credit_card",
            accent_color=VERIFY_ACCENT,
            icon_size=40,
            height=100
        )

        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.pack(fill="both", expand=True, padx=30, pady=(0, 20))

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
        # Filter row
        # -------------------------
        filter_card = ctk.CTkFrame(wrapper, corner_radius=15, border_width=1, border_color="#E5E8EC")
        filter_card.pack(fill="x", pady=(0, 15))

        ctk.CTkFrame(filter_card, height=6, corner_radius=0, fg_color=VERIFY_ACCENT).pack(fill="x", side="top")

        filter_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        filter_row.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(filter_row, text="Status:", font=("Arial", 13, "bold")).pack(side="left", padx=(0, 8))

        self.status_filter = ctk.CTkComboBox(
            filter_row,
            values=["All", "Approved", "Rejected"],
            width=160,
            command=lambda choice: self.load_loans()
        )
        self.status_filter.set("All")
        self.status_filter.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            filter_row,
            text="🔄 Refresh",
            fg_color="transparent",
            border_width=1,
            border_color="#D1D5DB",
            text_color="#374151",
            hover_color="#F3F4F6",
            command=self.load_loans
        ).pack(side="left")

        # -------------------------
        # Table
        # -------------------------
        table_card = ctk.CTkFrame(wrapper, corner_radius=15, border_width=1, border_color="#E5E8EC")
        table_card.pack(fill="both", expand=True)

        ctk.CTkFrame(table_card, height=6, corner_radius=0, fg_color=VERIFY_ACCENT).pack(fill="x", side="top")

        table_inner = ctk.CTkFrame(table_card, fg_color="transparent")
        table_inner.pack(fill="both", expand=True, padx=15, pady=15)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Loan.Treeview",
            background="white", fieldbackground="white",
            foreground="#111827", rowheight=32,
            font=("Arial", 12), borderwidth=0
        )
        style.configure(
            "Loan.Treeview.Heading",
            background=VERIFY_ACCENT, foreground="white",
            font=("Arial", 12, "bold"), borderwidth=0
        )
        style.map("Loan.Treeview", background=[("selected", "#F3E8FF")])

        columns = ("ID", "Username", "Type", "Amount", "Duration", "Interest", "Status", "Remarks")

        self.tree = ttk.Treeview(
            table_inner, columns=columns, show="headings",
            height=16, style="Loan.Treeview"
        )

        widths = {"ID": 50, "Username": 120, "Type": 130, "Amount": 100,
                  "Duration": 90, "Interest": 80, "Status": 100, "Remarks": 180}

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center", width=widths.get(col, 120))

        scrollbar = ttk.Scrollbar(table_inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        # -------------------------
        # Action buttons
        # -------------------------
        action_row = ctk.CTkFrame(wrapper, fg_color="transparent")
        action_row.pack(fill="x", pady=(15, 0))

        self.selected_label = ctk.CTkLabel(
            action_row, text="No loan selected", font=("Arial", 13), text_color="#6B7280"
        )
        self.selected_label.pack(side="left")

        ctk.CTkButton(
            action_row,
            text="✅  Approve",
            fg_color="#16A34A",
            hover_color="#15803D",
            command=lambda: self.set_status("Approved")
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            action_row,
            text="❌  Reject",
            fg_color="#DC2626",
            hover_color="#B91C1C",
            command=lambda: self.set_status("Rejected")
        ).pack(side="right")

        self.load_loans()

    # -------------------------
    # Load / filter loans
    # -------------------------
    def load_loans(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        self.selected_loan_id = None
        self.selected_label.configure(text="No loan selected")

        status = self.status_filter.get()

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        if status == "All":
            cursor.execute("""
                SELECT loans.id, users.username, loans.loan_type, loans.amount,
                       loans.duration, loans.interest, loans.status, loans.remarks
                FROM loans
                JOIN users ON users.id = loans.user_id
                ORDER BY loans.id DESC
            """)
        else:
            cursor.execute("""
                SELECT loans.id, users.username, loans.loan_type, loans.amount,
                       loans.duration, loans.interest, loans.status, loans.remarks
                FROM loans
                JOIN users ON users.id = loans.user_id
                WHERE loans.status = ?
                ORDER BY loans.id DESC
            """, (status,))

        rows = cursor.fetchall()
        conn.close()

        for row in rows:
            self.tree.insert("", "end", values=row)

    def on_select(self, event=None):
        selection = self.tree.selection()
        if not selection:
            self.selected_loan_id = None
            self.selected_label.configure(text="No loan selected")
            return

        values = self.tree.item(selection[0], "values")
        self.selected_loan_id = values[0]
        self.selected_label.configure(
            text=f"Selected: Loan #{values[0]} — {values[1]} ({values[2]})"
        )

    # -------------------------
    # Approve / Reject override
    # -------------------------
    def set_status(self, new_status):

        if not self.selected_loan_id:
            messagebox.showerror("Error", "Select a loan first.")
            return

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE loans SET status=? WHERE id=?",
            (new_status, self.selected_loan_id)
        )

        conn.commit()
        conn.close()

        messagebox.showinfo("Updated", f"Loan #{self.selected_loan_id} marked as {new_status}.")

        self.load_loans()

    def go_back(self):
        self.master.show_admin_dashboard()