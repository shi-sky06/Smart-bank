import customtkinter as ctk
from tkinter import messagebox
import sqlite3
import os
import platform
import subprocess
from PIL import Image

from assets.ui_helpers import build_hero_header
from assets.icon_loader import get_icon

VERIFY_ACCENT = "#D97706"

STATUS_COLORS = {
    "Pending": ("#FEF3C7", "#B45309"),
    "Verified": ("#DCFCE7", "#15803D"),
    "Rejected": ("#FEE2E2", "#B91C1C"),
}

IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")


class DocumentVerificationPage(ctk.CTkFrame):

    def __init__(self, master):
        super().__init__(master)

        self.master = master
        self._thumbnail_cache = {}
        self._group_state = {}   # loan_id -> expanded (bool)
        self._group_bodies = {}  # loan_id -> body frame
        self._group_arrows = {}  # loan_id -> arrow label

        self.configure(fg_color="#F9FAFB")
        self.pack(fill="both", expand=True)

        build_hero_header(
            self,
            title="Document Verification",
            subtitle="Review documents grouped by loan application",
            icon_name="scroll",
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
            values=["Pending", "Verified", "Rejected", "All"],
            width=160,
            command=lambda choice: self.load_documents()
        )
        self.status_filter.set("Pending")
        self.status_filter.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            filter_row,
            text="🔄 Refresh",
            fg_color="transparent",
            border_width=1,
            border_color="#D1D5DB",
            text_color="#374151",
            hover_color="#F3F4F6",
            command=self.load_documents
        ).pack(side="left")

        # -------------------------
        # Scrollable list of loan groups
        # -------------------------
        self.groups_container = ctk.CTkScrollableFrame(wrapper, fg_color="transparent")
        self.groups_container.pack(fill="both", expand=True)

        self.load_documents()

    # =========================
    # Load + group documents by loan
    # =========================
    def load_documents(self):

        for widget in self.groups_container.winfo_children():
            widget.destroy()

        self._group_state.clear()
        self._group_bodies.clear()
        self._group_arrows.clear()

        status = self.status_filter.get()

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        base_query = """
            SELECT loan_documents.id, loan_documents.loan_id, users.username,
                   loans.loan_type, loan_documents.document_type,
                   loan_documents.status, loan_documents.file_path
            FROM loan_documents
            JOIN loans ON loans.id = loan_documents.loan_id
            JOIN users ON users.id = loans.user_id
        """

        if status == "All":
            cursor.execute(base_query + " ORDER BY loan_documents.loan_id DESC, loan_documents.id ASC")
        else:
            cursor.execute(
                base_query + " WHERE loan_documents.status = ? ORDER BY loan_documents.loan_id DESC, loan_documents.id ASC",
                (status,)
            )

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            ctk.CTkLabel(
                self.groups_container,
                text="No documents match this filter.",
                font=("Arial", 14),
                text_color="#6B7280"
            ).pack(pady=40)
            return

        # Group by loan_id, preserving query order
        groups = {}
        for doc_id, loan_id, username, loan_type, doc_type, doc_status, file_path in rows:
            groups.setdefault(loan_id, {
                "username": username,
                "loan_type": loan_type,
                "docs": []
            })
            groups[loan_id]["docs"].append((doc_id, doc_type, doc_status, file_path))

        for loan_id, data in groups.items():
            self._build_loan_group(loan_id, data)

    # =========================
    # One collapsible loan group
    # =========================
    def _build_loan_group(self, loan_id, data):

        card = ctk.CTkFrame(
            self.groups_container, corner_radius=15,
            fg_color="white", border_width=1, border_color="#E5E8EC"
        )
        card.pack(fill="x", pady=8)

        ctk.CTkFrame(card, height=5, corner_radius=0, fg_color=VERIFY_ACCENT).pack(fill="x", side="top")

        # ---- Header (click to expand/collapse) ----
        header = ctk.CTkFrame(card, fg_color="transparent", cursor="hand2")
        header.pack(fill="x", padx=15, pady=12)

        arrow = ctk.CTkLabel(header, text="▼", font=("Arial", 13, "bold"), text_color="#6B7280", width=20)
        arrow.pack(side="left", padx=(0, 8))
        self._group_arrows[loan_id] = arrow

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            title_col,
            text=f"Loan #{loan_id} — {data['username']}",
            font=("Arial", 15, "bold"),
            text_color="#111827",
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_col,
            text=data["loan_type"],
            font=("Arial", 12),
            text_color="#6B7280",
            anchor="w"
        ).pack(anchor="w")

        # Status summary counts
        counts = {}
        for _, _, doc_status, _ in data["docs"]:
            counts[doc_status] = counts.get(doc_status, 0) + 1

        summary_text = "  ·  ".join(f"{v} {k}" for k, v in counts.items())
        ctk.CTkLabel(
            header, text=summary_text, font=("Arial", 12, "bold"), text_color="#6B7280"
        ).pack(side="right", padx=10)

        # ---- Body (documents) ----
        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=15, pady=(0, 15))
        self._group_bodies[loan_id] = body
        self._group_state[loan_id] = True  # expanded by default

        for doc_id, doc_type, doc_status, file_path in data["docs"]:
            self._build_document_row(body, doc_id, doc_type, doc_status, file_path)

        def toggle(event=None):
            expanded = self._group_state[loan_id]
            if expanded:
                body.pack_forget()
                arrow.configure(text="▶")
            else:
                body.pack(fill="x", padx=15, pady=(0, 15))
                arrow.configure(text="▼")
            self._group_state[loan_id] = not expanded

        header.bind("<Button-1>", toggle)
        title_col.bind("<Button-1>", toggle)
        for child in title_col.winfo_children():
            child.bind("<Button-1>", toggle)

    # =========================
    # One document row (thumbnail/badge + status + actions)
    # =========================
    def _build_document_row(self, parent, doc_id, doc_type, doc_status, file_path):

        row = ctk.CTkFrame(parent, fg_color="#F9FAFB", corner_radius=10)
        row.pack(fill="x", pady=4)

        # ---- Thumbnail (images) or file-type badge (PDF/other) ----
        preview_frame = ctk.CTkFrame(row, width=48, height=48, corner_radius=8, fg_color="#E5E7EB")
        preview_frame.pack(side="left", padx=10, pady=10)
        preview_frame.pack_propagate(False)

        thumb = self._get_thumbnail(file_path)
        if thumb:
            ctk.CTkLabel(preview_frame, image=thumb, text="").place(relx=0.5, rely=0.5, anchor="center")
        else:
            ext = os.path.splitext(file_path or "")[1].replace(".", "").upper() or "FILE"
            ctk.CTkLabel(
                preview_frame, text=ext, font=("Arial", 10, "bold"), text_color="#374151"
            ).place(relx=0.5, rely=0.5, anchor="center")

        # ---- Doc type (lean — no loan info repeated per row) ----
        ctk.CTkLabel(
            row, text=doc_type, font=("Arial", 14, "bold"), text_color="#111827"
        ).pack(side="left", padx=(5, 15))

        # ---- Status pill ----
        bg, fg = STATUS_COLORS.get(doc_status, ("#F3F4F6", "#374151"))
        pill = ctk.CTkLabel(
            row, text=doc_status, font=("Arial", 11, "bold"),
            text_color=fg, fg_color=bg, corner_radius=10, width=80, height=24
        )
        pill.pack(side="left", padx=(0, 10))

        # ---- Actions ----
        action_frame = ctk.CTkFrame(row, fg_color="transparent")
        action_frame.pack(side="right", padx=10, pady=8)

        ctk.CTkButton(
            action_frame, text="📂 Open", width=70, height=28,
            fg_color="#2563EB", hover_color="#1D4ED8", font=("Arial", 11),
            command=lambda: self.open_file(file_path)
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            action_frame, text="✅", width=36, height=28,
            fg_color="#16A34A", hover_color="#15803D", font=("Arial", 12),
            command=lambda: self.set_status(doc_id, "Verified")
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            action_frame, text="❌", width=36, height=28,
            fg_color="#DC2626", hover_color="#B91C1C", font=("Arial", 12),
            command=lambda: self.set_status(doc_id, "Rejected")
        ).pack(side="left", padx=3)

    # =========================
    # Thumbnail generator (images only)
    # =========================
    def _get_thumbnail(self, file_path):

        if not file_path or not os.path.exists(file_path):
            return None

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in IMAGE_EXTENSIONS:
            return None

        if file_path in self._thumbnail_cache:
            return self._thumbnail_cache[file_path]

        try:
            pil_img = Image.open(file_path)
            pil_img.thumbnail((44, 44))
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            self._thumbnail_cache[file_path] = ctk_img
            return ctk_img
        except Exception:
            return None

    # =========================
    # Open file with OS default viewer
    # =========================
    def open_file(self, file_path):

        if not file_path or not os.path.exists(file_path):
            messagebox.showerror("Error", "File not found on disk.")
            return

        try:
            system = platform.system()
            if system == "Windows":
                os.startfile(file_path)
            elif system == "Darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    # =========================
    # Verify / Reject
    # =========================
    def set_status(self, doc_id, new_status):

        conn = sqlite3.connect("bank.db")
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE loan_documents SET status=? WHERE id=?",
            (new_status, doc_id)
        )

        conn.commit()
        conn.close()

        self.load_documents()

    def go_back(self):
        self.master.show_admin_dashboard()