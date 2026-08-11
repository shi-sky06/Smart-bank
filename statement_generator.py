"""
statement_generator.py

Builds a branded PDF bank statement using reportlab, given a user's
info and their transaction rows. Used by the "Download Statement"
button on the Transactions page.
"""

import os
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

NAVY = colors.HexColor("#1E3A8A")
GREEN = colors.HexColor("#16A34A")
RED = colors.HexColor("#DC2626")
BLUE = colors.HexColor("#2563EB")
MUTED = colors.HexColor("#6B7280")
LIGHT_ROW = colors.HexColor("#F9FAFB")

LOGO_PATH = os.path.join(
    os.path.dirname(__file__), "assets", "icons", "bank_logo.png"
)


def _amount_color(transaction_type: str):
    t = (transaction_type or "").lower()
    if "deposit" in t:
        return GREEN
    if "withdraw" in t:
        return RED
    if "transfer" in t:
        return BLUE
    return colors.black


def generate_statement_pdf(user_name, username, account_id, balance,
                            transactions, output_path):
    """
    transactions: list of (transaction_type, receiver, amount, date) tuples,
    same shape as returned by TransactionsPage.load_transactions()'s query.
    """

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "StatementTitle", parent=styles["Title"],
        textColor=NAVY, fontSize=20, spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        "StatementSubtitle", parent=styles["Normal"],
        textColor=MUTED, fontSize=10, spaceAfter=14
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"], textColor=MUTED, fontSize=9
    )
    value_style = ParagraphStyle(
        "Value", parent=styles["Normal"], textColor=colors.black,
        fontSize=12, spaceAfter=6
    )

    story = []

    # -------------------------
    # Header: logo + title
    # -------------------------
    if os.path.exists(LOGO_PATH):
        try:
            logo = Image(LOGO_PATH, width=0.6 * inch, height=0.6 * inch)
            header_table = Table(
                [[logo, Paragraph("SmartBank AI — Account Statement", title_style)]],
                colWidths=[0.8 * inch, 5.5 * inch]
            )
            header_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(header_table)
        except Exception:
            story.append(Paragraph("SmartBank AI — Account Statement", title_style))
    else:
        story.append(Paragraph("SmartBank AI — Account Statement", title_style))

    story.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        subtitle_style
    ))
    story.append(Spacer(1, 10))

    # -------------------------
    # Account summary block
    # -------------------------
    summary_data = [
        [Paragraph("ACCOUNT HOLDER", label_style), Paragraph("ACCOUNT ID", label_style),
         Paragraph("USERNAME", label_style), Paragraph("CURRENT BALANCE", label_style)],
        [Paragraph(str(user_name), value_style), Paragraph(str(account_id), value_style),
         Paragraph(str(username), value_style),
         Paragraph(f"₹{balance:,.2f}", value_style)],
    ]

    summary_table = Table(summary_data, colWidths=[1.7 * inch] * 4)
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("LINEBELOW", (0, 1), (-1, 1), 1, colors.HexColor("#E5E8EC")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # -------------------------
    # Transactions table
    # -------------------------
    story.append(Paragraph("Transaction History", ParagraphStyle(
        "SectionHeader", parent=styles["Heading2"], textColor=NAVY, fontSize=14
    )))
    story.append(Spacer(1, 8))

    if not transactions:
        story.append(Paragraph("No transactions found.", styles["Normal"]))
    else:
        table_data = [["Date", "Type", "Receiver", "Amount"]]

        row_styles = []

        for i, (t_type, receiver, amount, date) in enumerate(transactions, start=1):
            table_data.append([
                str(date),
                str(t_type),
                str(receiver) if receiver else "-",
                f"₹{amount:,.2f}",
            ])
            row_styles.append(("TEXTCOLOR", (3, i), (3, i), _amount_color(t_type)))

        txn_table = Table(
            table_data,
            colWidths=[1.7 * inch, 1.3 * inch, 2.2 * inch, 1.3 * inch],
            repeatRows=1
        )

        base_style = [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E8EC")),
        ]

        for i in range(1, len(table_data)):
            if i % 2 == 0:
                base_style.append(("BACKGROUND", (0, i), (-1, i), LIGHT_ROW))

        txn_table.setStyle(TableStyle(base_style + row_styles))
        story.append(txn_table)

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "This is a system-generated statement from SmartBank AI. "
        "For queries, contact SmartBank support.",
        ParagraphStyle("Footer", parent=styles["Normal"], textColor=MUTED, fontSize=8)
    ))

    doc.build(story)
    return output_path