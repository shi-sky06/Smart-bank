import re
import random
import os
import sqlite3
from datetime import datetime

import session
from ai import chat_history
from ai.banking_ai import (
    get_spending_summary,
    get_nudges,
    get_smallest_transaction,
    get_largest_transaction,
    get_extreme_transaction_filtered,
    get_transactions_filtered
)


# ============================================================
# Gemini setup
# ============================================================

_gemini_ready = False
_gemini_client = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google import genai

    _api_key = os.getenv("GEMINI_API_KEY")

    if _api_key:
        _gemini_client = genai.Client(api_key=_api_key)
        _gemini_ready = True

except ImportError:
    pass


# ============================================================
# Rule-based intents
# ============================================================

INTENTS = [

    {
        "name": "greeting",
        "patterns": [
            "hi", "hello", "hey", "good morning", "good afternoon",
            "good evening", "yo", "sup", "hiya"
        ],
        "replies": [
            "Hello! I'm Milo, your SmartBank AI Assistant. How can I help you today?",
            "Hey there! What can I do for you today?",
            "Hi! Ask me about deposits, withdrawals, transfers, loans, or your balance."
        ],
        "action": None,
    },

    {
        "name": "balance",
        "patterns": [
            "balance", "bank balance", "account balance", "how much money",
            "how much do i have", "check balance", "my balance"
        ],
        "replies": [
            "Sure! I can show your account balance on the Dashboard.",
            "You can view your current balance from the Dashboard page.",
        ],
        "action": "balance",
    },

    {
        "name": "deposit",
        "patterns": [
            "deposit", "add money", "put money", "add funds",
            "deposit money", "make a deposit"
        ],
        "replies": [
            "Sure! To make a deposit, open the Deposit page, enter the amount you want to add, and click Confirm Deposit.",
            "Let's get your deposit done! Go to Deposit → enter the amount → confirm the transaction. Your account balance will be updated automatically.",
        ],
        "action": "deposit",
    },

    {
        "name": "withdraw",
        "patterns": [
            "withdraw", "withdrawal", "take out money", "cash out",
            "withdraw money", "get cash"
        ],
        "replies": [
            "Sure! To withdraw money, open the Withdraw page, enter the amount you want to withdraw, and click Confirm Withdrawal.",
            "Let's get your withdrawal done! Go to Withdraw → enter the amount → confirm the transaction. Your account balance will be updated automatically.",
        ],
        "action": "withdraw",
    },

    {
        "name": "transfer",
        "patterns": [
            "transfer", "send money", "move money", "transfer funds",
            "send funds", "pay someone", "wire money"
        ],
        "replies": [
            "Sure! To transfer money, open the Transfer page, enter the recipient's username, enter the amount, and click Confirm Transfer.",
            "Let's get your transfer done! Go to Transfer → enter the recipient's username → enter the amount → confirm the transaction. Your balance will be updated automatically.",
        ],
        "action": "transfer",
    },

    {
        "name": "loan",
        "patterns": [
            "apply for loan", "apply loan", "need a loan", "new loan",
            "take a loan", "borrow money"
        ],
        "replies": [
            "Sure! To apply for a loan, open the Loans page, select the loan type, enter the required amount and details, upload the required documents, and submit your application.",
            "Let's get your loan application started! Go to Loans → select the loan type → enter the amount and required details → upload your documents → submit the application.",
        ],
        "action": "loan",
    },

    {
        "name": "transactions",
        "patterns": [
            "transactions", "transaction history", "recent transactions",
            "spending history", "statement", "activity"
        ],
        "replies": [
            "Sure! To view your transactions, open the Transactions page to see your recent deposits, withdrawals, and transfers.",
            "Let's review your transaction history! Go to Transactions → view your recent deposits, withdrawals, and transfers → select a transaction if you need more details.",
        ],
        "action": "transactions",
    },

    {
        "name": "documents_needed",
        "patterns": [
            "documents needed", "what documents", "documents required",
            "documents for loan", "id proof"
        ],
        "replies": [
            "For a loan application you'll need to upload three documents: "
            "an ID Proof (like Aadhaar), an Income Proof, and a Bank Statement. "
            "You can upload these directly on the Loans page."
        ],
        "action": None,
    },

    {
        "name": "interest_rate",
        "patterns": [
            "interest rate", "what is the interest", "loan interest",
            "how much interest"
        ],
        "replies": [
            "SmartBank currently offers loans at a flat 8.5% annual interest rate. "
            "You can see an estimated EMI on the Loans page as you enter an amount and duration."
        ],
        "action": None,
    },

    {
        "name": "security",
        "patterns": [
            "is my money safe", "is this secure", "security", "safe to use",
            "data privacy", "is smartbank safe"
        ],
        "replies": [
            "Your account is protected with password-based authentication, and all "
            "transactions are logged for your review on the Transactions page. "
            "If anything looks unfamiliar, contact support right away."
        ],
        "action": None,
    },

    {
        "name": "close_account",
        "patterns": [
            "close my account", "close account", "delete my account",
            "delete account", "deactivate account"
        ],
        "replies": [
            "Closing an account isn't something I can do directly from chat, for "
            "your security. Please contact SmartBank support or visit a branch, "
            "and an administrator will help you close your account safely."
        ],
        "action": None,
    },

    {
        "name": "contact_support",
        "patterns": [
            "contact support", "customer support", "help desk",
            "talk to a human", "speak to someone"
        ],
        "replies": [
            "For anything I can't help with, you can reach SmartBank support "
            "through the email associated with your account, or visit a branch in person."
        ],
        "action": None,
    },

    {
        "name": "thanks",
        "patterns": ["thanks", "thank you", "appreciate it", "cheers"],
        "replies": [
            "You're welcome! Let me know if there's anything else you need.",
            "Anytime! I'm here if you need more help.",
        ],
        "action": None,
    },

    {
        "name": "goodbye",
        "patterns": ["bye", "goodbye", "see you", "later", "exit", "quit"],
        "replies": ["Goodbye! Have a great day.", "See you next time!"],
        "action": None,
    },

    {
        "name": "help",
        "patterns": ["help", "what can you do", "options", "services", "menu"],
        "replies": [
            "I can help you with:\n"
            "• Deposits\n"
            "• Withdrawals\n"
            "• Transfers\n"
            "• Loans\n"
            "• Transactions\n"
            "• Checking your balance\n"
            "• Spending summary\n"
            "• Smallest transaction\n"
            "• Largest transaction\n"
            "• Transactions on a specific date (e.g. \"transactions on 2024-05-01\")\n"
            "• Transactions with a specific person (e.g. \"transactions with Priya\")\n"
            "• General banking questions\n\n"
            "What would you like to do?"
        ],
        "action": None,
    },
]


# ============================================================
# Special patterns
# ============================================================

LOAN_STATUS_PATTERNS = [
    "loan status", "my loan", "status of my loan",
    "loan application status", "check my loan"
]

SPENDING_PATTERNS = [
    "how much did i spend", "spending this month", "spending summary",
    "how much have i spent", "my spending", "spent this month"
]

SMALLEST_TRANSACTION_PATTERNS = [
    "smallest transaction", "smallest amount transaction", "smallest amount",
    "lowest transaction", "lowest amount transaction", "lowest amount",
    "least transaction", "least amount transaction",
    "least amount transaction done", "smallest transaction done",
    "lowest transaction done", "minimum transaction", "minimum amount",
    "smallest payment", "lowest payment"
]

LARGEST_TRANSACTION_PATTERNS = [
    "largest transaction", "largest amount transaction", "largest amount",
    "biggest transaction", "biggest amount transaction", "biggest amount",
    "highest transaction", "highest amount transaction", "highest amount",
    "maximum transaction", "maximum amount", "largest payment",
    "biggest payment"
]

DATE_TRANSACTION_TRIGGERS = [
    "transaction on", "transactions on", "transaction from",
    "transactions from", "on date", "for date", "did i spend on",
    "activity on"
]

NAME_TRANSACTION_TRIGGERS = [
    "transaction with", "transactions with", "transaction to",
    "transactions to", "transaction from", "transactions from",
    "payments to", "payment to", "sent to", "paid to", "money to",
    "involving"
]

NAME_STOPWORDS = {
    "please", "me", "my", "the", "a", "an", "show", "find", "get",
    "did", "i", "send", "sent", "pay", "paid", "to", "with", "from",
    "name", "named", "called", "person", "someone", "of", "for", "on"
}

MONTH_NAMES = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9,
    "october": 10, "oct": 10, "november": 11, "nov": 11, "december": 12, "dec": 12,
}

_MONTH_ALTERNATION = "|".join(sorted(MONTH_NAMES.keys(), key=len, reverse=True))
TRANSACTION_WORD_RE = re.compile(r"\btransactions?\b")

YES_WORDS = {"yes", "yeah", "yep", "sure", "ok", "okay", "please", "go ahead"}
NO_WORDS = {"no", "nope", "nah", "not now", "cancel"}

_last_action = {"pending": None}


# ============================================================
# Small shared helpers
# ============================================================

def _reply(text, action=None):
    """Shorthand for the {"reply": ..., "action": ...} shape every
    handler returns -- avoids repeating the same 4-line dict literal
    everywhere."""
    return {"reply": text, "action": action}


def _finalize(username, result):
    """Logs the bot's reply to chat history (if logged in) and returns
    it -- avoids repeating the same log-then-return block after every
    handler call in ask_assistant()."""
    if username:
        chat_history.append_message(username, "milo", result["reply"])
    return result


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _get_current_username():
    try:
        return session.current_user[2]
    except (TypeError, IndexError):
        return None


def _match_intent(message: str):
    text = _normalize(message)
    best_intent, best_score = None, 0
    for intent in INTENTS:
        for pattern in intent["patterns"]:
            if pattern in text and len(pattern) > best_score:
                best_intent, best_score = intent, len(pattern)
    return best_intent


def _normalize_year(year_str):
    """Turns a 2-digit year into a 4-digit one (26 -> 2026); else current year."""
    if not year_str:
        return datetime.now().year
    year = int(year_str)
    return year + 2000 if year < 100 else year


def _extract_date(text: str):
    """
    Pulls a date out of free text and normalizes it to YYYY-MM-DD.
    Supports ISO (2024-05-01), slash DD/MM/YYYY, and written dates like
    "10 aug 26" / "10-aug-26" / "aug 10 2026" (full or abbreviated month
    names, space/dash separators, optional ordinal suffix, 2- or 4-digit
    year). Returns None if nothing recognizable is found.
    """
    day_pattern = r"(\d{1,2})(?:st|nd|rd|th)?"

    patterns = [
        (r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", lambda m: (int(m[1]), int(m[2]), int(m[3]))),
        (r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", lambda m: (int(m[3]), int(m[2]), int(m[1]))),
        (r"\b" + day_pattern + r"[\s\-]+(" + _MONTH_ALTERNATION + r")\.?[\s\-]*,?\s*(\d{2,4})?\b",
         lambda m: (_normalize_year(m[3]), MONTH_NAMES[m[2]], int(m[1]))),
        (r"\b(" + _MONTH_ALTERNATION + r")\.?[\s\-]+" + day_pattern + r"\s*,?\s*(\d{2,4})?\b",
         lambda m: (_normalize_year(m[3]), MONTH_NAMES[m[1]], int(m[2]))),
    ]

    for pattern, to_ymd in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                year, month, day = to_ymd(match)
                return datetime(year, month, day).strftime("%Y-%m-%d")
            except (ValueError, KeyError):
                continue

    return None


def _extract_name(text: str, trigger: str):
    """
    Pulls the name out right after `trigger` (e.g. "transactions with"),
    stopping at the first stopword/month-name it hits so combined queries
    like "with zoya on 10 aug 2026" correctly extract just "zoya".
    """
    idx = text.find(trigger)
    if idx == -1:
        return None

    after = text[idx + len(trigger):].strip()
    if not after:
        return None

    name_words = []
    for tok in re.findall(r"[a-zA-Z]+", after):
        if tok in NAME_STOPWORDS or tok in MONTH_NAMES:
            if name_words:
                break
            continue
        name_words.append(tok)
        if len(name_words) == 2:
            break

    return " ".join(name_words).title() if name_words else None


# ============================================================
# Unified transaction query handler
# Detects THREE independent signals -- extremum (smallest/largest),
# name, and date -- and routes to whichever combination applies:
# "largest transaction with zoya", "transactions on 10 aug 2026",
# "largest transaction with zoya on 10 aug 2026", etc.
# ============================================================

def _detect_extremum(text: str):
    if any(p in text for p in SMALLEST_TRANSACTION_PATTERNS):
        return "asc"
    if any(p in text for p in LARGEST_TRANSACTION_PATTERNS):
        return "desc"
    return None


def _detect_name(text: str):
    for trigger in NAME_TRANSACTION_TRIGGERS:
        if trigger in text:
            name = _extract_name(text, trigger)
            if name:
                return name
    return None


def _handle_transaction_query(message: str):

    text = _normalize(message)
    mentions_transaction = bool(TRANSACTION_WORD_RE.search(text))
    has_date_trigger = any(t in text for t in DATE_TRANSACTION_TRIGGERS)
    has_name_trigger = any(t in text for t in NAME_TRANSACTION_TRIGGERS)

    order = _detect_extremum(text)
    name = _detect_name(text)
    date = _extract_date(text) if (mentions_transaction or has_date_trigger) else None

    if order is None and name is None and date is None and not mentions_transaction:
        return None

    if has_date_trigger and date is None and order is None and name is None:
        return _reply(
            "I can look up transactions for a specific date — "
            "try something like \"transactions on 2024-05-01\" "
            "or \"transactions on 10 aug 2026\"."
        )

    if has_name_trigger and name is None and order is None and date is None:
        return _reply(
            "Who would you like to look up transactions for? "
            "Try something like \"transactions with Priya\"."
        )

    if not session.current_user:
        return _reply("Please log in first to check your transactions.")

    if order and (name or date):
        return _reply(get_extreme_transaction_filtered(order, name=name, date=date))
    if order:
        return _reply(get_smallest_transaction() if order == "asc" else get_largest_transaction())
    if name or date:
        return _reply(get_transactions_filtered(name=name, date=date))

    # Just mentions "transaction(s)" with no specifics -- let the normal
    # "transactions" intent handle the recent-5 list.
    return None


# ============================================================
# Loan status
# ============================================================

def _handle_loan_status(message: str):

    text = _normalize(message)
    if not any(p in text for p in LOAN_STATUS_PATTERNS):
        return None

    if not session.current_user:
        return _reply("Please log in to check your loan status.")

    user_id = session.current_user[0]

    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT loan_type, amount, duration, interest, status, remarks
        FROM loans
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,)
    )
    loan = cursor.fetchone()
    conn.close()

    if not loan:
        return _reply(
            "You haven't applied for any loans yet. "
            "Want me to open the Loans page?"
        )

    loan_type, amount, duration, interest, status, remarks = loan
    monthly_rate = interest / 12 / 100

    if monthly_rate > 0:
        emi = (
            amount * monthly_rate * (1 + monthly_rate) ** duration
            / ((1 + monthly_rate) ** duration - 1)
        )
    else:
        emi = amount / duration

    status_emoji = "🟢" if status == "Approved" else "🔴"

    reply = (
        f"Your most recent loan application:\n\n"
        f"Type: {loan_type}\n"
        f"Amount: ₹{amount:,.2f}\n"
        f"Duration: {duration} months\n"
        f"Status: {status} {status_emoji}\n"
        f"Remarks: {remarks}\n"
    )
    if status == "Approved":
        reply += f"Estimated Monthly EMI: ₹{emi:,.2f}"

    return _reply(reply)


# ============================================================
# Spending summary
# ============================================================

def _handle_spending_summary(message: str):

    text = _normalize(message)
    if not any(p in text for p in SPENDING_PATTERNS):
        return None

    if not session.current_user:
        return _reply("Please log in to see your spending summary.")

    summary = get_spending_summary(days=30)
    if not summary:
        return _reply("You haven't made any outgoing transactions in the last 30 days.")

    breakdown_lines = "\n".join(f"- {t}: ₹{amt:,.2f}" for t, amt in summary["breakdown"].items())
    raw_summary = (
        f"Total spent in the last 30 days: ₹{summary['total']:,.2f} "
        f"across {summary['count']} transactions.\n{breakdown_lines}"
    )

    reply = raw_summary

    if _gemini_ready:
        try:
            prompt = (
                "You are Milo, SmartBank's assistant. "
                "Rephrase this raw spending data as a short, "
                "friendly 2-3 sentence summary. Mention the total "
                "and call out the biggest category. "
                "Don't invent numbers not given below.\n\n" + raw_summary
            )
            response = _gemini_client.models.generate_content(
                model="gemini-flash-latest", contents=prompt
            )
            if response and response.text:
                reply = response.text.strip()
        except Exception:
            pass

    return _reply(reply)


# ============================================================
# Startup nudges
# ============================================================

def get_startup_nudges():
    return get_nudges()


# ============================================================
# Gemini fallback
# ============================================================

def _ask_gemini(message: str):

    if not _gemini_ready:
        return None

    try:
        prompt = (
            "You are Milo, a friendly and concise AI assistant for SmartBank, "
            "a banking app. Answer the user's question in 2-4 short sentences. "
            "Do not give specific financial or investment advice. "
            "For banking actions such as deposit, withdraw, transfer, and loans, "
            "direct the user to the appropriate SmartBank page. "
            f"User's message: {message}"
        )
        response = _gemini_client.models.generate_content(
            model="gemini-flash-latest", contents=prompt
        )
        return response.text.strip() if response and response.text else None

    except Exception as e:
        print(f"[Gemini error] {type(e).__name__}: {e}")
        return None


_FALLBACK_HELP_TEXT = (
    "I'm not sure I understood that. "
    "You can ask me about:\n"
    "• Deposits\n"
    "• Withdrawals\n"
    "• Transfers\n"
    "• Loans\n"
    "• Transactions\n"
    "• Spending summary\n"
    "• Smallest transaction\n"
    "• Largest transaction\n"
    "• Transactions on a specific date\n"
    "• Transactions with a specific person\n"
    "• Banking services\n\n"
    "Try something like \"check my balance\" or \"what is my largest transaction\"."
)


# ============================================================
# Main assistant
# ============================================================

# Handlers tried in order (before the generic intent list / Gemini
# fallback). Each takes the raw message and returns a result dict or
# None if it doesn't apply. Order matters: transaction queries must be
# checked before loan/spending since some phrasings could overlap.
_QUERY_HANDLERS = (
    _handle_transaction_query,
    _handle_loan_status,
    _handle_spending_summary,
)


def ask_assistant(message: str):

    username = _get_current_username()

    if username:
        chat_history.append_message(username, "user", message)

    text = _normalize(message)

    # --- Yes / No follow-up on a previously offered action ---
    if _last_action["pending"]:
        if text in YES_WORDS or any(w in text for w in YES_WORDS):
            action = _last_action["pending"]
            _last_action["pending"] = None
            return _finalize(username, _reply("Great, opening that for you now.", action))

        if text in NO_WORDS or any(w in text for w in NO_WORDS):
            _last_action["pending"] = None
            return _finalize(username, _reply("No problem! Let me know if you need anything else."))

    # --- Transaction queries / loan status / spending summary ---
    # Checked before generic intents so they aren't swallowed by the
    # broader "transactions" keyword match.
    for handler in _QUERY_HANDLERS:
        result = handler(message)
        if result:
            return _finalize(username, result)

    # --- Normal rule-based intents ---
    intent = _match_intent(message)
    if intent:
        reply = random.choice(intent["replies"])
        if intent["action"]:
            _last_action["pending"] = intent["action"]
            reply += "\n\nWould you like me to open that for you? (yes/no)"
        return _finalize(username, _reply(reply))

    # --- Gemini fallback ---
    _last_action["pending"] = None
    gemini_reply = _ask_gemini(message)
    return _finalize(username, _reply(gemini_reply or _FALLBACK_HELP_TEXT))