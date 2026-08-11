"""
achievements.py

Calculates gamified banking badges using the existing
users, transactions, and loans tables in bank.db.

No additional database tables are required.

Badges:
- First Deposit      : Completed at least one deposit
- Smart Saver        : Current balance >= ₹25,000
- Consistent Saver   : Made deposits on at least 3 different days
- Loan Approved      : Has at least one approved loan
- Transfer Pro       : Completed 5 or more transfers
- Active Banker      : Completed 20 or more transactions
"""

import sqlite3


# ============================================================
# BADGE DEFINITIONS
# ============================================================

BADGE_DEFINITIONS = [
    {
        "key": "first_deposit",
        "label": "First Deposit",
        "description": "Completed your first deposit",
        "icon": "wave",
        "color": "#16A34A",
        "bg": "#DCFCE7",
    },
    {
        "key": "smart_saver",
        "label": "Smart Saver",
        "description": "Maintained a balance of ₹25,000 or more",
        "icon": "money_bag",
        "color": "#D97706",
        "bg": "#FEF3C7",
    },
    {
        "key": "consistent_saver",
        "label": "Consistent Saver",
        "description": "Made deposits on 3 different days",
        "icon": "chart_up",
        "color": "#2563EB",
        "bg": "#DBEAFE",
    },
    {
        "key": "loan_approved",
        "label": "Loan Approved",
        "description": "Received approval for a loan",
        "icon": "credit_card",
        "color": "#9333EA",
        "bg": "#F3E8FF",
    },
    {
        "key": "transfer_pro",
        "label": "Transfer Pro",
        "description": "Completed 5 or more transfers",
        "icon": "repeat",
        "color": "#0EA5E9",
        "bg": "#E0F2FE",
    },
    {
        "key": "active_banker",
        "label": "Active Banker",
        "description": "Completed 20 or more transactions",
        "icon": "bar_chart",
        "color": "#DC2626",
        "bg": "#FEE2E2",
    },
]


# ============================================================
# GET USER ACHIEVEMENTS
# ============================================================

def get_user_achievements(user_id):
    """
    Returns all badges with an 'unlocked' boolean.

    Example:
    [
        {
            "key": "first_deposit",
            "label": "First Deposit",
            "description": "Completed your first deposit",
            "icon": "wave",
            "color": "#16A34A",
            "bg": "#DCFCE7",
            "unlocked": True
        }
    ]
    """

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    # ========================================================
    # 1. FIRST DEPOSIT
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'Deposit'
        """,
        (user_id,)
    )

    deposit_count = cursor.fetchone()[0]

    first_deposit = deposit_count >= 1

    # ========================================================
    # 2. SMART SAVER
    # ========================================================

    cursor.execute(
        """
        SELECT balance
        FROM users
        WHERE id = ?
        """,
        (user_id,)
    )

    row = cursor.fetchone()

    balance = row[0] if row else 0

    smart_saver = balance >= 25000

    # ========================================================
    # 3. CONSISTENT SAVER
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(DISTINCT date(date))
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'Deposit'
        """,
        (user_id,)
    )

    deposit_days = cursor.fetchone()[0]

    consistent_saver = deposit_days >= 3

    # ========================================================
    # 4. LOAN APPROVED
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM loans
        WHERE user_id = ?
        AND status = 'Approved'
        """,
        (user_id,)
    )

    approved_loans = cursor.fetchone()[0]

    loan_approved = approved_loans >= 1

    # ========================================================
    # 5. TRANSFER PRO
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = ?
        AND transaction_type = 'Transfer'
        """,
        (user_id,)
    )

    transfer_count = cursor.fetchone()[0]

    transfer_pro = transfer_count >= 5

    # ========================================================
    # 6. ACTIVE BANKER
    # ========================================================

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,)
    )

    total_transactions = cursor.fetchone()[0]

    active_banker = total_transactions >= 20

    # ========================================================
    # CLOSE DATABASE
    # ========================================================

    conn.close()

    # ========================================================
    # UNLOCKED STATUS
    # ========================================================

    unlocked_map = {
        "first_deposit": first_deposit,
        "smart_saver": smart_saver,
        "consistent_saver": consistent_saver,
        "loan_approved": loan_approved,
        "transfer_pro": transfer_pro,
        "active_banker": active_banker,
    }

    # ========================================================
    # BUILD RESULT
    # ========================================================

    result = []

    for badge in BADGE_DEFINITIONS:

        badge_copy = dict(badge)

        badge_copy["unlocked"] = unlocked_map.get(
            badge["key"],
            False
        )

        result.append(badge_copy)

    return result