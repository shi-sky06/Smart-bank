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


def get_transactions_by_date(date):
    """
    Returns all of the user's transactions on a specific date.
    `date` should be an ISO string: YYYY-MM-DD.
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
          AND date(date) = date(?)
        ORDER BY date DESC
        """,
        (user_id, date)
    )

    transactions = cursor.fetchall()

    conn.close()

    if not transactions:
        return f"No transactions found on {date}."

    result = f"📅 Transactions on {date}\n\n"

    for transaction_type, receiver, amount, d in transactions:

        if receiver:
            result += (
                f"• {transaction_type} → {receiver} | "
                f"₹{amount:,.2f} | {d}\n"
            )
        else:
            result += (
                f"• {transaction_type} | "
                f"₹{amount:,.2f} | {d}\n"
            )

    return result


def get_transactions_by_name(name):
    """
    Returns all of the user's transactions where the receiver's name
    matches (partial, case-insensitive match).
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
          AND receiver LIKE ?
        ORDER BY date DESC
        """,
        (user_id, f"%{name}%")
    )

    transactions = cursor.fetchall()

    conn.close()

    if not transactions:
        return f"No transactions found involving '{name}'."

    result = f"👤 Transactions with {name}\n\n"

    for transaction_type, receiver, amount, d in transactions:
        result += (
            f"• {transaction_type} → {receiver} | "
            f"₹{amount:,.2f} | {d}\n"
        )

    return result


# ============================================================
# Shared filter builder
# Used by get_transactions_filtered, get_extreme_transaction_filtered,
# and get_transaction_aggregate so the WHERE-clause / context-string
# logic for name, single date, date range, transaction type, and
# amount range only needs to be written once.
# ============================================================

def _build_filter_conditions(user_id, name=None, date=None, date_from=None,
                              date_to=None, types=None, amount_min=None,
                              amount_max=None):

    conditions = ["user_id=?"]
    params = [user_id]

    if name:
        conditions.append("receiver LIKE ?")
        params.append(f"%{name}%")

    if date:
        conditions.append("date(date) = date(?)")
        params.append(date)

    if date_from:
        conditions.append("date(date) >= date(?)")
        params.append(date_from)

    if date_to:
        conditions.append("date(date) <= date(?)")
        params.append(date_to)

    if types:
        like_clauses = " OR ".join(["transaction_type LIKE ?"] * len(types))
        conditions.append(f"({like_clauses})")
        params.extend(f"%{t}%" for t in types)

    if amount_min is not None:
        conditions.append("amount >= ?")
        params.append(amount_min)

    if amount_max is not None:
        conditions.append("amount <= ?")
        params.append(amount_max)

    return conditions, params


def _filter_context(name=None, date=None, date_from=None, date_to=None,
                     types=None, amount_min=None, amount_max=None):

    parts = []

    if types:
        parts.append(f"({'/'.join(types)})")
    if name:
        parts.append(f"with {name}")
    if date:
        parts.append(f"on {date}")
    if date_from and date_to:
        parts.append(f"between {date_from} and {date_to}")
    elif date_from:
        parts.append(f"from {date_from} onward")
    elif date_to:
        parts.append(f"up to {date_to}")
    if amount_min is not None and amount_max is not None:
        parts.append(f"between ₹{amount_min:,.2f} and ₹{amount_max:,.2f}")
    elif amount_min is not None:
        parts.append(f"over ₹{amount_min:,.2f}")
    elif amount_max is not None:
        parts.append(f"under ₹{amount_max:,.2f}")

    return (" " + " ".join(parts)) if parts else ""


def get_extreme_transaction_filtered(order, name=None, date=None, date_from=None,
                                      date_to=None, types=None, amount_min=None,
                                      amount_max=None):
    """
    Returns the user's smallest (order='asc') or largest (order='desc')
    transaction, optionally narrowed down by any combination of
    receiver name, a specific date, a date range, transaction type(s),
    and/or an amount range.
    """

    if session.current_user is None:
        return "Please login first."

    user_id = session.current_user[0]

    conditions, params = _build_filter_conditions(
        user_id, name=name, date=date, date_from=date_from, date_to=date_to,
        types=types, amount_min=amount_min, amount_max=amount_max
    )
    where_clause = " AND ".join(conditions)
    sql_order = "ASC" if order == "asc" else "DESC"

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT transaction_type, receiver, amount, date
        FROM transactions
        WHERE {where_clause}
        ORDER BY amount {sql_order}
        LIMIT 1
        """,
        params
    )

    transaction = cursor.fetchone()

    conn.close()

    context = _filter_context(
        name=name, date=date, date_from=date_from, date_to=date_to,
        types=types, amount_min=amount_min, amount_max=amount_max
    )

    if not transaction:
        return f"No transactions found{context}."

    transaction_type, receiver, amount, d = transaction
    label = "smallest" if order == "asc" else "largest"
    emoji = "💸" if order == "asc" else "💰"

    if receiver:
        return (
            f"{emoji} Your {label} transaction{context} was "
            f"₹{amount:,.2f} ({transaction_type} → {receiver}) "
            f"on {d}."
        )

    return (
        f"{emoji} Your {label} transaction{context} was "
        f"₹{amount:,.2f} ({transaction_type}) "
        f"on {d}."
    )


def get_transactions_filtered(name=None, date=None, date_from=None, date_to=None,
                               types=None, amount_min=None, amount_max=None):
    """
    Returns a list of the user's transactions, optionally narrowed down
    by any combination of receiver name, a specific date, a date range,
    transaction type(s), and/or an amount range. If nothing is passed
    this behaves like a full (unlimited) transaction list.
    """

    if session.current_user is None:
        return "Please login first."

    user_id = session.current_user[0]

    conditions, params = _build_filter_conditions(
        user_id, name=name, date=date, date_from=date_from, date_to=date_to,
        types=types, amount_min=amount_min, amount_max=amount_max
    )
    where_clause = " AND ".join(conditions)

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT transaction_type, receiver, amount, date
        FROM transactions
        WHERE {where_clause}
        ORDER BY date DESC
        """,
        params
    )

    transactions = cursor.fetchall()

    conn.close()

    context = _filter_context(
        name=name, date=date, date_from=date_from, date_to=date_to,
        types=types, amount_min=amount_min, amount_max=amount_max
    )

    if not transactions:
        return f"No transactions found{context}."

    result = f"📜 Transactions{context}\n\n"

    for transaction_type, receiver, amount, d in transactions:

        if receiver:
            result += (
                f"• {transaction_type} → {receiver} | "
                f"₹{amount:,.2f} | {d}\n"
            )
        else:
            result += (
                f"• {transaction_type} | "
                f"₹{amount:,.2f} | {d}\n"
            )

    return result


def get_transaction_aggregate(mode, name=None, date=None, date_from=None,
                               date_to=None, types=None, amount_min=None,
                               amount_max=None):
    """
    Returns a count ("count") or a total sum ("sum") of the user's
    transactions matching the given filters -- e.g. "how many
    withdrawals this month" or "total spent on transfers".
    """

    if session.current_user is None:
        return "Please login first."

    user_id = session.current_user[0]

    conditions, params = _build_filter_conditions(
        user_id, name=name, date=date, date_from=date_from, date_to=date_to,
        types=types, amount_min=amount_min, amount_max=amount_max
    )
    where_clause = " AND ".join(conditions)

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT COUNT(*), COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE {where_clause}
        """,
        params
    )

    count, total = cursor.fetchone()

    conn.close()

    context = _filter_context(
        name=name, date=date, date_from=date_from, date_to=date_to,
        types=types, amount_min=amount_min, amount_max=amount_max
    )

    if not count:
        return f"No transactions found{context}."

    plural = "s" if count != 1 else ""

    if mode == "count":
        return f"🔢 You have {count} transaction{plural}{context}."

    return f"➕ {count} transaction{plural}{context}, totaling ₹{total:,.2f}."


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