import customtkinter as ctk
from tkinter import messagebox, filedialog
import sqlite3
import session

from assets.ui_helpers import build_hero_header, PAGE_COLORS
from assets.icon_loader import get_icon

INTEREST_RATE = 8.5  # annual %, matches the rate used in apply_loan


class LoanPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.configure(fg_color="transparent")

        # Hero Header
        build_hero_header(
            self,
            title="SmartBank Loan Center",
            subtitle="Apply for a loan and get instant eligibility results",
            icon_name="credit_card",
            accent_color=PAGE_COLORS["loan"],
            icon_size=40,
            height=100
        )

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=40)
        scroll.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(scroll, corner_radius=15)
        card.grid(row=0, column=0, pady=(0, 20), sticky="ew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkFrame(
            card, height=6, corner_radius=0, fg_color=PAGE_COLORS["loan"]
        ).grid(row=0, column=0, sticky="ew")

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.grid(row=1, column=0, pady=20, padx=20)

        self.loan_type = ctk.CTkComboBox(
            inner,
            values=[
                "Personal Loan",
                "Home Loan",
                "Education Loan",
                "Vehicle Loan"
            ],
            width=300
        )
        self.loan_type.pack(pady=10)
        self.loan_type.set("Personal Loan")

        self.amount_entry = ctk.CTkEntry(
            inner,
            width=300,
            placeholder_text="💵  Loan Amount"
        )
        self.amount_entry.pack(pady=10)
        self.amount_entry.bind("<KeyRelease>", self.update_emi_estimate)

        self.duration_entry = ctk.CTkEntry(
            inner,
            width=300,
            placeholder_text="📅  Duration (Months)"
        )
        self.duration_entry.pack(pady=10)
        self.duration_entry.bind("<KeyRelease>", self.update_emi_estimate)

        # Store uploaded documents
        self.documents = {}

        ctk.CTkButton(
            inner,
            text="📄  Upload Aadhaar / ID Proof",
            width=280,
            fg_color="transparent",
            border_width=1,
            border_color="#D1D5DB",
            text_color="#374151",
            hover_color="#F3F4F6",
            command=lambda: self.upload_document("ID Proof")
        ).pack(pady=5)

        ctk.CTkButton(
            inner,
            text="📄  Upload Income Proof",
            width=280,
            fg_color="transparent",
            border_width=1,
            border_color="#D1D5DB",
            text_color="#374151",
            hover_color="#F3F4F6",
            command=lambda: self.upload_document("Income Proof")
        ).pack(pady=5)

        ctk.CTkButton(
            inner,
            text="📄  Upload Bank Statement",
            width=280,
            fg_color="transparent",
            border_width=1,
            border_color="#D1D5DB",
            text_color="#374151",
            hover_color="#F3F4F6",
            command=lambda: self.upload_document("Bank Statement")
        ).pack(pady=5)

        ctk.CTkButton(
            inner,
            text="Apply Loan",
            width=220,
            fg_color=PAGE_COLORS["loan"],
            hover_color="#7E22CE",
            command=self.apply_loan
        ).pack(pady=20)

        self.status_label = ctk.CTkLabel(
            inner,
            text="",
            font=("Arial", 14, "bold"),
            justify="left"
        )
        self.status_label.pack(pady=10)

        # =========================
        # EMI Estimate Card
        # =========================
        emi_card = ctk.CTkFrame(scroll, corner_radius=15)
        emi_card.grid(row=1, column=0, pady=(0, 30), sticky="ew")
        emi_card.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkFrame(
            emi_card, height=6, corner_radius=0, fg_color="#16A34A"
        ).grid(row=0, column=0, columnspan=2, sticky="ew")

        header_row = ctk.CTkFrame(emi_card, fg_color="transparent")
        header_row.grid(row=1, column=0, columnspan=2, pady=(18, 15))

        chart_icon = get_icon("bar_chart", size=20)
        if chart_icon:
            ctk.CTkLabel(header_row, image=chart_icon, text="").pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            header_row,
            text="Loan Repayment Estimate",
            font=("Arial", 17, "bold"),
            text_color="#111827"
        ).pack(side="left")

        self.emi_principal_label = self._emi_stat(emi_card, 2, 0, "Principal", "₹0.00")
        self.emi_rate_label = self._emi_stat(emi_card, 2, 1, "Interest Rate", f"{INTEREST_RATE}% p.a.")
        self.emi_tenure_label = self._emi_stat(emi_card, 3, 0, "Tenure", "0 months")
        self.emi_monthly_label = self._emi_stat(emi_card, 3, 1, "Est. Monthly EMI", "₹0.00", highlight=True)
        self.emi_total_label = self._emi_stat(emi_card, 4, 0, "Total Payable", "₹0.00")
        self.emi_interest_label = self._emi_stat(emi_card, 4, 1, "Total Interest", "₹0.00")

        ctk.CTkLabel(
            emi_card,
            text="This is an estimate only. Final approval depends on your credit eligibility.",
            font=("Arial", 11),
            text_color="#6B7280"
        ).grid(row=5, column=0, columnspan=2, pady=(10, 18))

    # =========================
    # EMI stat block helper
    # =========================
    def _emi_stat(self, parent, row, column, label, value, highlight=False):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=column, pady=8, padx=25, sticky="w")

        ctk.CTkLabel(
            wrap, text=label.upper(), font=("Arial", 11, "bold"), text_color="#6B7280"
        ).pack(anchor="w")

        value_label = ctk.CTkLabel(
            wrap,
            text=value,
            font=("Arial", 18, "bold"),
            text_color="#16A34A" if highlight else "#111827"
        )
        value_label.pack(anchor="w")

        return value_label

    # =========================
    # Live EMI calculation
    # =========================
    def update_emi_estimate(self, event=None):
        amount_str = self.amount_entry.get().strip()
        duration_str = self.duration_entry.get().strip()

        try:
            principal = float(amount_str)
            months = int(duration_str)

            if principal <= 0 or months <= 0:
                raise ValueError

            monthly_rate = INTEREST_RATE / 12 / 100

            if monthly_rate > 0:
                emi = principal * monthly_rate * (1 + monthly_rate) ** months / \
                      ((1 + monthly_rate) ** months - 1)
            else:
                emi = principal / months

            total_payable = emi * months
            total_interest = total_payable - principal

            self.emi_principal_label.configure(text=f"₹ {principal:,.2f}")
            self.emi_tenure_label.configure(text=f"{months} months")
            self.emi_monthly_label.configure(text=f"₹ {emi:,.2f}")
            self.emi_total_label.configure(text=f"₹ {total_payable:,.2f}")
            self.emi_interest_label.configure(text=f"₹ {total_interest:,.2f}")

        except (ValueError, ZeroDivisionError):
            self.emi_principal_label.configure(text="₹ 0.00")
            self.emi_tenure_label.configure(text="0 months")
            self.emi_monthly_label.configure(text="₹ 0.00")
            self.emi_total_label.configure(text="₹ 0.00")
            self.emi_interest_label.configure(text="₹ 0.00")

    # =========================
    # Document Upload
    # =========================

    def upload_document(self, doc_type):

        file = filedialog.askopenfilename(
            filetypes=[
                ("PDF Files", "*.pdf"),
                ("Image Files", "*.png *.jpg *.jpeg")
            ]
        )

        if file:

            self.documents[doc_type] = file

            messagebox.showinfo(
                "Uploaded",
                f"{doc_type} uploaded successfully"
            )

    # =========================
    # Loan Application
    # =========================

    def apply_loan(self):

        loan_type = self.loan_type.get()

        amount = self.amount_entry.get()

        duration = self.duration_entry.get()

        if amount == "" or duration == "":

            messagebox.showerror(
                "Error",
                "Fill all details"
            )

            return

        required_documents = [
            "ID Proof",
            "Income Proof",
            "Bank Statement"
        ]

        for doc in required_documents:

            if doc not in self.documents:

                messagebox.showerror(
                    "Missing Document",
                    f"Please upload {doc}"
                )

                return

        try:

            loan_amount = float(amount)

            duration = int(duration)

            conn = sqlite3.connect("bank.db")

            cursor = conn.cursor()

            user_id = session.current_user[0]

            cursor.execute(
                """
                SELECT id,balance
                FROM users
                WHERE id=?
                """,
                (user_id,)
            )

            user = cursor.fetchone()

            if user is None:

                messagebox.showerror(
                    "Error",
                    "User not found"
                )

                conn.close()
                return

            balance = user[1]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM transactions
                WHERE user_id=?
                """,
                (user_id,)
            )

            transaction_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM loans
                WHERE user_id=? AND status='Approved'
                """,
                (user_id,)
            )

            active_loan = cursor.fetchone()[0]

            credit_score = 0

            if balance >= 50000:
                credit_score += 40

            elif balance >= 20000:
                credit_score += 30

            elif balance >= 10000:
                credit_score += 20

            if transaction_count >= 20:
                credit_score += 40

            elif transaction_count >= 10:
                credit_score += 30

            elif transaction_count >= 5:
                credit_score += 20

            if active_loan == 0:

                credit_score += 20

            status = "Approved"

            remarks = "Eligible"

            if credit_score < 60:

                status = "Rejected"

                remarks = f"Low Credit Score ({credit_score}/100)"

            elif loan_amount > balance * 5:

                status = "Rejected"

                remarks = "Loan amount exceeds eligibility"

            interest = INTEREST_RATE

            cursor.execute(
                """
                INSERT INTO loans
                (user_id,loan_type,amount,duration,interest,status,remarks)
                VALUES(?,?,?,?,?,?,?)
                """,
                (
                    user_id,
                    loan_type,
                    loan_amount,
                    duration,
                    interest,
                    status,
                    remarks
                )
            )

            loan_id = cursor.lastrowid

            for doc_type, path in self.documents.items():

                cursor.execute(
                    """
                    INSERT INTO loan_documents
                    (loan_id,document_type,file_path,status)
                    VALUES(?,?,?,?)
                    """,
                    (
                        loan_id,
                        doc_type,
                        path,
                        "Pending"
                    )
                )

            conn.commit()

            conn.close()

            # EMI for the confirmation message
            monthly_rate = INTEREST_RATE / 12 / 100
            if monthly_rate > 0:
                emi = loan_amount * monthly_rate * (1 + monthly_rate) ** duration / \
                      ((1 + monthly_rate) ** duration - 1)
            else:
                emi = loan_amount / duration

            if status == "Approved":

                messagebox.showinfo(
                    "Loan Approved",
                    f"Loan Approved\nCredit Score: {credit_score}/100\n"
                    f"Estimated Monthly EMI: ₹{emi:,.2f}"
                )

                self.status_label.configure(
                    text=(
                        f"Loan Status: Approved 🟢\n"
                        f"Credit Score: {credit_score}/100\n"
                        f"Estimated Monthly EMI: ₹{emi:,.2f}"
                    ),
                    text_color="#16A34A"
                )

            else:

                messagebox.showerror(
                    "Loan Rejected",
                    remarks
                )

                self.status_label.configure(
                    text=f"Loan Status: Rejected 🔴\n{remarks}",
                    text_color="#DC2626"
                )

        except ValueError:

            messagebox.showerror(
                "Error",
                "Enter valid numbers"
            )