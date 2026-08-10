"""
achievements.py

Computes which gamified badges a user has unlocked, based on their
existing data in bank.db. No new tables needed — everything is
derived from users / transactions / loans, which already exist.

Badge criteria (kept achievable with the current schema):
- First Deposit     : made at least one Deposit
- Big Saver         : current balance >= 50,000
- Steady Saver      : no Withdraw transactions in the last 30 days
- Loan Approved     : has at least one Approved loan
- Transfer Pro      : made 5+ Transfer transactions
- Active User       : 20+ total transactions

Note: a "Loan Paid Off" badge isn't possible yet since the current
loans table doesn't track repayment/closure — only approval status.
Happy to add that if you want a real repayment tracking feature later.
"""

import sqlite3


BADGE_DEFINITIONS = [
    {
        "key": "first_deposit",
        "label": "First Deposit",
        "description": "Made your first deposit",
        "icon": "wave",
        "color": "#16A34A",
        "bg": "#DCFCE7",
    },
    {
        "key": "big_saver",
        "label": "Big Saver",
        "description": "Balance reached ₹50,000",
        "icon": "money_bag",
        "color": "#D97706",
        "bg": "#FEF3C7",
    },
    {
        "key": "steady_saver",
        "label": "Steady Saver",
        "description": "No withdrawals in the last 30 days",
        "icon": "chart_up",
        "color": "#2563EB",
        "bg": "#DBEAFE",
    },
    {
        "key": "loan_approved",
        "label": "Loan Approved",
        "description": "Got a loan approved",
        "icon": "credit_card",
        "color": "#9333EA",
        "bg": "#F3E8FF",
    },
    {
        "key": "transfer_pro",
        "label": "Transfer Pro",
        "description": "Made 5+ transfers",
        "icon": "repeat",
        "color": "#0EA5E9",
        "bg": "#E0F2FE",
    },
    {
        "key": "active_user",
        "label": "Active User",
        "description": "20+ total transactions",
        "icon": "bar_chart",
        "color": "#DC2626",
        "bg": "#FEE2E2",
    },
]


def get_user_achievements(user_id):
    """
    Returns BADGE_DEFINITIONS with an extra "unlocked" bool per badge.
    """
    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM transactions WHERE user_id=? AND transaction_type='Deposit'",
        (user_id,)
    )
    has_deposit = cursor.fetchone()[0] > 0

    cursor.execute("SELECT balance FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    balance = row[0] if row else 0
    big_saver = balance >= 50000

    cursor.execute(
        """
        SELECT COUNT(*) FROM transactions
        WHERE user_id=? AND transaction_type='Withdraw'
        AND date >= date('now', '-30 days')
        """,
        (user_id,)
    )
    recent_withdraws = cursor.fetchone()[0]
    steady_saver = recent_withdraws == 0 and has_deposit

    cursor.execute(
        "SELECT COUNT(*) FROM loans WHERE user_id=? AND status='Approved'",
        (user_id,)
    )
    loan_approved = cursor.fetchone()[0] > 0

    cursor.execute(
        "SELECT COUNT(*) FROM transactions WHERE user_id=? AND transaction_type='Transfer'",
        (user_id,)
    )
    transfer_count = cursor.fetchone()[0]
    transfer_pro = transfer_count >= 5

    cursor.execute(
        "SELECT COUNT(*) FROM transactions WHERE user_id=?",
        (user_id,)
    )
    total_txns = cursor.fetchone()[0]
    active_user = total_txns >= 20

    conn.close()

    unlocked_map = {
        "first_deposit": has_deposit,
        "big_saver": big_saver,
        "steady_saver": steady_saver,
        "loan_approved": loan_approved,
        "transfer_pro": transfer_pro,
        "active_user": active_user,
    }

    result = []
    for badge in BADGE_DEFINITIONS:
        badge_copy = dict(badge)
        badge_copy["unlocked"] = unlocked_map.get(badge["key"], False)
        result.append(badge_copy)

    return result