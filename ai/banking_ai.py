import sqlite3
import session


def get_balance():

    if session.current_user is None:
        return "Please login first."

    user_id = session.current_user[0]

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT balance
        FROM users
        WHERE id=?
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    conn.close()

    if result:
        return f"💰 Your current balance is ₹{result[0]:,.2f}"

    return "Account not found."


def get_transactions():

    if session.current_user is None:
        return "Please login first."

    user_id = session.current_user[0]

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT transaction_type,
               receiver,
               amount,
               date
        FROM transactions
        WHERE user_id=?
        ORDER BY date DESC
        LIMIT 5
        """,
        (user_id,)
    )

    transactions = cursor.fetchall()

    conn.close()

    if not transactions:
        return "No recent transactions."

    result = "📜 Your Recent Transactions\n\n"

    for transaction_type, receiver, amount, date in transactions:

        if receiver:
            result += (
                f"• {transaction_type} → {receiver} | "
                f"₹{amount:,.2f} | {date}\n"
            )
        else:
            result += (
                f"• {transaction_type} | "
                f"₹{amount:,.2f} | {date}\n"
            )

    return result


def get_spending_summary(days=30):
    """
    Returns spending totals for the last `days` days.
    Only counts non-Deposit transactions as spending.
    """

    if session.current_user is None:
        return None

    user_id = session.current_user[0]

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT transaction_type, amount
        FROM transactions
        WHERE user_id=?
          AND date >= date('now', ?)
          AND transaction_type != 'Deposit'
        """,
        (user_id, f"-{days} days")
    )

    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return None

    breakdown = {}
    total = 0.0

    for transaction_type, amount in rows:

        breakdown[transaction_type] = (
            breakdown.get(transaction_type, 0.0) + amount
        )

        total += amount

    return {
        "total": total,
        "breakdown": breakdown,
        "count": len(rows),
        "days": days,
    }


def get_smallest_transaction():
    """
    Returns the user's smallest transaction.
    """

    if session.current_user is None:
        return "Please login first."

    user_id = session.current_user[0]

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT transaction_type,
               receiver,
               amount,
               date
        FROM transactions
        WHERE user_id=?
        ORDER BY amount ASC
        LIMIT 1
        """,
        (user_id,)
    )

    transaction = cursor.fetchone()

    conn.close()

    if not transaction:
        return "No transactions found."

    transaction_type, receiver, amount, date = transaction

    if receiver:
        return (
            f"💸 Your smallest transaction was "
            f"₹{amount:,.2f} ({transaction_type} → {receiver}) "
            f"on {date}."
        )

    return (
        f"💸 Your smallest transaction was "
        f"₹{amount:,.2f} ({transaction_type}) "
        f"on {date}."
    )


def get_largest_transaction():
    """
    Returns the user's largest transaction.
    """

    if session.current_user is None:
        return "Please login first."

    user_id = session.current_user[0]

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT transaction_type,
               receiver,
               amount,
               date
        FROM transactions
        WHERE user_id=?
        ORDER BY amount DESC
        LIMIT 1
        """,
        (user_id,)
    )

    transaction = cursor.fetchone()

    conn.close()

    if not transaction:
        return "No transactions found."

    transaction_type, receiver, amount, date = transaction

    if receiver:
        return (
            f"💰 Your largest transaction was "
            f"₹{amount:,.2f} ({transaction_type} → {receiver}) "
            f"on {date}."
        )

    return (
        f"💰 Your largest transaction was "
        f"₹{amount:,.2f} ({transaction_type}) "
        f"on {date}."
    )


def get_nudges():
    """
    Returns a list of short nudge strings for proactive display.
    Empty list if nothing noteworthy.
    """

    if session.current_user is None:
        return []

    user_id = session.current_user[0]
    nudges = []

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    # Low balance check
    cursor.execute(
        "SELECT balance FROM users WHERE id=?",
        (user_id,)
    )

    row = cursor.fetchone()
    balance = row[0] if row else None

    LOW_BALANCE_THRESHOLD = 500

    if balance is not None and balance < LOW_BALANCE_THRESHOLD:
        nudges.append(
            f"⚠️ Heads up — your balance is a bit low "
            f"(₹{balance:,.2f}). "
            f"Want me to open the Deposit page?"
        )

    # Unusually large transaction vs. recent typical size
    cursor.execute(
        """
        SELECT amount
        FROM transactions
        WHERE user_id=?
          AND transaction_type != 'Deposit'
        ORDER BY date DESC
        LIMIT 20
        """,
        (user_id,)
    )

    recent = [r[0] for r in cursor.fetchall()]

    conn.close()

    if len(recent) >= 5:

        latest = recent[0]
        typical = sum(recent[1:]) / len(recent[1:])

        if typical > 0 and latest > typical * 3:
            nudges.append(
                f"👀 Your most recent transaction "
                f"(₹{latest:,.2f}) is much larger "
                f"than your usual (~₹{typical:,.2f}). "
                f"Just flagging it in case that wasn't you!"
            )

    return nudges
