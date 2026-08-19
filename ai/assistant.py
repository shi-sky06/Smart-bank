import re
import random
import os
import sqlite3
from datetime import datetime, timedelta

import session
from ai import chat_history
from ai.banking_ai import (
    get_spending_summary,
    get_nudges,
    get_smallest_transaction,
    get_largest_transaction,
    get_extreme_transaction_filtered,
    get_transactions_filtered,
    get_transaction_aggregate,
)


# ============================================================
# Ollama setup
# ============================================================
# Replaces the old Gemini client. Ollama runs locally (default
# http://localhost:11434) and needs no API key -- just the daemon
# running (`ollama serve`, usually auto-started after install) and a
# model pulled (`ollama pull llama3.1`, or whatever you set below).
#
# Configure via .env or environment variables:
#   OLLAMA_HOST  -- default http://localhost:11434
#   OLLAMA_MODEL -- default llama3.1

_ollama_ready = False
_ollama_model = "llama3.2:1b" 
_ollama_host = "http://localhost:11434"
_requests = None

try:
    from dotenv import load_dotenv, find_dotenv
    # find_dotenv() walks upward from this file's own location, not the
    # process's current working directory -- so this still finds .env
    # even if the app is launched from a shortcut, IDE, or another folder.
    _dotenv_path = find_dotenv(filename=".env", usecwd=False)
    if not _dotenv_path:
        # Fallback: look next to this file / project root explicitly.
        _dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    load_dotenv(_dotenv_path)
    print(f"[Milo startup] .env loaded from: {_dotenv_path}")
except ImportError:
    print("[Milo startup] python-dotenv not installed; skipping .env load")

_ollama_model = os.getenv("OLLAMA_MODEL", _ollama_model)
_ollama_host = os.getenv("OLLAMA_HOST", _ollama_host).rstrip("/")

try:
    import requests as _requests

    try:
        _resp = _requests.get(f"{_ollama_host}/api/tags", timeout=2)
        if _resp.status_code == 200:
            _available_models = [m.get("name", "") for m in _resp.json().get("models", [])]
            _model_present = any(
                m == _ollama_model or m.startswith(_ollama_model + ":")
                for m in _available_models
            )
            if _model_present or not _available_models:
                _ollama_ready = True
                print(f"[Milo startup] Ollama ready at {_ollama_host} (model={_ollama_model})")
            else:
                print(
                    f"[Milo startup] Ollama is running but '{_ollama_model}' isn't pulled. "
                    f"Run: ollama pull {_ollama_model}  -- Ollama disabled until then."
                )
        else:
            print(f"[Milo startup] Ollama responded with status {_resp.status_code} -- disabled")
    except _requests.exceptions.RequestException as e:
        print(
            f"[Milo startup] Could not reach Ollama at {_ollama_host} "
            f"({type(e).__name__}). Is 'ollama serve' running? -- Ollama disabled"
        )

except ImportError:
    print("[Milo startup] 'requests' not installed (pip install requests) -- Ollama disabled")


def _ollama_generate(prompt: str):
    """
    Sends a single-turn prompt to the local Ollama server and returns the
    model's text response, or None on failure / if Ollama isn't ready.
    This is the drop-in replacement for the old
    `_gemini_client.models.generate_content(...)` call -- every call site
    below just swapped that line for `_ollama_generate(prompt)`.
    """
    if not _ollama_ready:
        return None
    try:
        response = _requests.post(
            f"{_ollama_host}/api/generate",
            json={
                "model": _ollama_model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        text = data.get("response")
        return text.strip() if text else None
    except Exception as e:
        print(f"[Ollama error] {type(e).__name__}: {e}")
        return None


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
            "• Transactions (by type, date, date range, person, or amount)\n"
            "• Checking your balance\n"
            "• Spending summary\n"
            "• Smallest / largest transaction\n"
            "• Totals and counts (e.g. \"how many withdrawals this month\")\n"
            "• General banking questions\n\n"
            "What would you like to do?"
        ],
        "action": None,
    },
]

_INTENTS_BY_NAME = {intent["name"]: intent for intent in INTENTS}


# ============================================================
# Special patterns
# ============================================================

LOAN_STATUS_PATTERNS = [
    "loan status", "my loan", "status of my loan",
    "loan application status", "check my loan"
]

LOAN_LIST_PATTERNS = [
    "all my loans", "list my loans", "my loans", "loan history", "all loans"
]

LOAN_DUE_PATTERNS = [
    "next emi due", "emi due date", "when is my next payment",
    "when is my emi due", "next payment due date", "next installment due",
    "when is my next emi"
]

LOAN_OWE_PATTERNS = [
    "how much do i owe", "how much i owe", "total i owe",
    "outstanding amount", "loan balance", "amount remaining",
    "how much left to pay", "total payable", "remaining balance on my loan",
    "how much do i still owe"
]

LOAN_EMI_PATTERNS = [
    "my emi", "monthly emi", "loan emi", "what is my emi",
    "how much is my emi", "monthly payment", "installment amount",
    "my monthly installment"
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

# Maps a keyword found in the message to the LIKE search term(s) used
# against the transaction_type column. Checked in order, so more
# specific phrases (e.g. "international transfer") are matched before
# their broader substrings (e.g. "transfer").
TYPE_KEYWORDS = [
    ("international transfer", ["International Transfer"]),
    ("intl transfer", ["International Transfer"]),
    ("transfer", ["Transfer"]),  # LIKE match also catches "International Transfer"
    ("withdrawal", ["Withdraw"]),
    ("withdraw", ["Withdraw"]),
    ("deposit", ["Deposit"]),
]

# Words that imply "extreme value" but aren't in the stricter phrase
# lists above (SMALLEST_TRANSACTION_PATTERNS / LARGEST_TRANSACTION_PATTERNS).
# Only used as a fallback, and only when a transaction-type keyword is
# also present -- e.g. "largest withdrawal" -- so a bare "highest" in an
# unrelated question (like "what's the highest interest rate") never
# gets misrouted into a transaction lookup.
EXTREMUM_WORDS_DESC = {"largest", "biggest", "highest", "maximum", "max"}
EXTREMUM_WORDS_ASC = {"smallest", "lowest", "least", "minimum", "min"}

# Words that signal "I want to look something up" rather than "I want
# to perform this action". Needed so a bare type keyword -- e.g.
# "withdraw" in "I want to withdraw money" -- doesn't get swallowed by
# the transaction-lookup handler and hijacked away from the normal
# "here's how to withdraw" action intent. A type keyword only counts as
# a lookup request on its own if paired with one of these.
QUERY_VERBS = {"show", "list", "view", "see", "what", "which", "how many"}

COUNT_PATTERNS = ["how many", "number of", "count of"]
SUM_PATTERNS = ["total", "how much did i", "how much have i", "sum of"]

RELATIVE_RANGE_PHRASES = ["today", "yesterday", "this week", "last week", "this month", "last month"]

# Recognizes an amount like "10000", "10,000", "₹10,000.50", or "10k".
AMOUNT_RE = r"₹?\s*([\d,]+(?:\.\d+)?)\s*(k|thousand)?"

YES_WORDS = {"yes", "yeah", "yep", "sure", "ok", "okay", "please", "go ahead"}
NO_WORDS = {"no", "nope", "nah", "not now", "cancel"}

# Pending confirmation / clarification state, keyed per-user (falls back
# to a shared "__anon__" bucket for logged-out sessions). Previously
# these were single global dicts shared by every user of the process,
# so one user's reply could trigger or complete a different user's
# pending action/question.
_last_action = {}
_pending_query = {}


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


def _pending_key(username):
    """Key used to isolate pending-action / pending-question state per
    user, so logged-in users never see or trigger each other's pending
    items. Logged-out sessions share one bucket, which is fine since
    only one anonymous session is expected at a time."""
    return username or "__anon__"


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


_DATE_PATTERNS = None


def _date_patterns():
    """Lazily built so _MONTH_ALTERNATION is available first."""
    global _DATE_PATTERNS
    if _DATE_PATTERNS is None:
        day_pattern = r"(\d{1,2})(?:st|nd|rd|th)?"
        _DATE_PATTERNS = [
            (r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", lambda m: (int(m[1]), int(m[2]), int(m[3]))),
            (r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", lambda m: (int(m[3]), int(m[2]), int(m[1]))),
            (r"\b" + day_pattern + r"[\s\-]+(" + _MONTH_ALTERNATION + r")\.?[\s\-]*,?\s*(\d{2,4})?\b",
             lambda m: (_normalize_year(m[3]), MONTH_NAMES[m[2]], int(m[1]))),
            (r"\b(" + _MONTH_ALTERNATION + r")\.?[\s\-]+" + day_pattern + r"\s*,?\s*(\d{2,4})?\b",
             lambda m: (_normalize_year(m[3]), MONTH_NAMES[m[1]], int(m[2]))),
        ]
    return _DATE_PATTERNS


def _extract_all_dates(text: str):
    """
    Finds every recognizable date in free text (ISO, slash DD/MM/YYYY,
    or written like "10 aug 26" / "aug 10 2026"), normalized to
    YYYY-MM-DD, in the order they appear. Used both for single-date
    extraction and for "between X and Y" ranges.
    """
    found = []
    for pattern, to_ymd in _date_patterns():
        for match in re.finditer(pattern, text):
            try:
                year, month, day = to_ymd(match)
                found.append((match.start(), datetime(year, month, day).strftime("%Y-%m-%d")))
            except (ValueError, KeyError):
                continue

    found.sort(key=lambda x: x[0])
    seen = set()
    ordered = []
    for _, d in found:
        if d not in seen:
            seen.add(d)
            ordered.append(d)
    return ordered


def _extract_date(text: str):
    dates = _extract_all_dates(text)
    return dates[0] if dates else None


def _last_month_range(today):
    first_this_month = today.replace(day=1)
    last_day_prev = first_this_month - timedelta(days=1)
    first_day_prev = last_day_prev.replace(day=1)
    return first_day_prev, last_day_prev


def _extract_date_range(text: str):
    """
    Recognizes relative ranges ("this month", "last week", "last 10
    days") and explicit "between <date> and <date>" ranges. Returns
    (date_from, date_to) as YYYY-MM-DD strings, or (None, None).
    """
    today = datetime.now().date()

    if "today" in text:
        return today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    if "yesterday" in text:
        y = today - timedelta(days=1)
        return y.strftime("%Y-%m-%d"), y.strftime("%Y-%m-%d")

    if "this week" in text:
        start = today - timedelta(days=today.weekday())
        return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    if "last week" in text:
        start = today - timedelta(days=today.weekday() + 7)
        end = today - timedelta(days=today.weekday() + 1)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    if "this month" in text:
        return today.replace(day=1).strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    if "last month" in text:
        start, end = _last_month_range(today)
        return start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")

    m = re.search(r"last\s+(\d+)\s+days?", text)
    if m:
        n = int(m.group(1))
        start = today - timedelta(days=n)
        return start.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

    if "between" in text:
        dates = _extract_all_dates(text)
        if len(dates) >= 2:
            return dates[0], dates[1]

    return None, None


def _parse_amount(num_str, suffix):
    val = float(num_str.replace(",", ""))
    if suffix and suffix.lower() in ("k", "thousand"):
        val *= 1000
    return val


def _extract_amount_range(text: str):
    """
    Recognizes amount comparisons: "over 10000", "above ₹5,000",
    "under 500", "less than 1k", "between 500 and 1000". Returns
    (amount_min, amount_max), either of which may be None.
    """
    m = re.search(r"between\s+" + AMOUNT_RE + r"\s+and\s+" + AMOUNT_RE, text)
    if m:
        low = _parse_amount(m.group(1), m.group(2))
        high = _parse_amount(m.group(3), m.group(4))
        return (min(low, high), max(low, high))

    m = re.search(r"(?:over|above|more than|greater than|at least)\s+" + AMOUNT_RE, text)
    if m:
        return (_parse_amount(m.group(1), m.group(2)), None)

    m = re.search(r"(?:under|below|less than|at most)\s+" + AMOUNT_RE, text)
    if m:
        return (None, _parse_amount(m.group(1), m.group(2)))

    return (None, None)


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
# Detects several independent signals -- extremum (smallest/largest),
# name, single date, date range, transaction type, amount range, and
# aggregate mode (sum/count) -- and composes whichever combination
# applies: "largest transfer to zoya last month", "how many withdrawals
# over 5000 this year", etc.
# ============================================================

def _detect_extremum(text: str, has_type: bool = False):
    if any(p in text for p in SMALLEST_TRANSACTION_PATTERNS):
        return "asc"
    if any(p in text for p in LARGEST_TRANSACTION_PATTERNS):
        return "desc"

    # Fallback: catches "largest withdrawal", "biggest deposit", etc.
    # Gated on has_type so it never fires on unrelated messages like
    # "what's the highest interest rate".
    if has_type:
        words = set(re.findall(r"[a-z]+", text))
        if words & EXTREMUM_WORDS_DESC:
            return "desc"
        if words & EXTREMUM_WORDS_ASC:
            return "asc"

    return None


def _detect_type(text: str):
    """Returns a list of LIKE search terms for transaction_type if the
    message names a specific kind of transaction (deposit, withdrawal,
    transfer, international transfer), else None."""
    for keyword, types in TYPE_KEYWORDS:
        if keyword in text:
            return types
    return None


def _detect_name(text: str):
    for trigger in NAME_TRANSACTION_TRIGGERS:
        if trigger in text:
            name = _extract_name(text, trigger)
            if name:
                return name
    return None


def _detect_aggregate_mode(text: str):
    if any(p in text for p in COUNT_PATTERNS):
        return "count"
    if any(p in text for p in SUM_PATTERNS):
        return "sum"
    return None


def _run_transaction_query(order=None, name=None, date=None, date_from=None,
                            date_to=None, types=None, amount_min=None,
                            amount_max=None, mode=None):
    """Shared routing logic: given whatever filters were detected (from
    the original message, or completed via slot-filling on a follow-up),
    decides which banking_ai function actually answers the question."""

    if not session.current_user:
        return _reply("Please log in first to check your transactions.")

    has_filters = any([
        name, date, date_from, date_to, types,
        amount_min is not None, amount_max is not None
    ])

    if mode:
        return _reply(get_transaction_aggregate(
            mode, name=name, date=date, date_from=date_from, date_to=date_to,
            types=types, amount_min=amount_min, amount_max=amount_max
        ))

    if order and has_filters:
        return _reply(get_extreme_transaction_filtered(
            order, name=name, date=date, date_from=date_from, date_to=date_to,
            types=types, amount_min=amount_min, amount_max=amount_max
        ))

    if order:
        return _reply(get_smallest_transaction() if order == "asc" else get_largest_transaction())

    if has_filters:
        return _reply(get_transactions_filtered(
            name=name, date=date, date_from=date_from, date_to=date_to,
            types=types, amount_min=amount_min, amount_max=amount_max
        ))

    return None


def _resolve_pending_query(pq: dict, message: str):
    """
    Attempts to fill in whatever slot was missing (a name or a date/date
    range) using the person's follow-up reply, then re-runs the original
    query with everything merged in. Returns None if the reply doesn't
    look like it answers the question, so the caller can fall back to
    treating it as a brand-new message instead.
    """
    text = _normalize(message)

    if pq["missing"] == "name":
        words = re.findall(r"[a-zA-Z]+", text)
        words = [w for w in words if w not in NAME_STOPWORDS]
        if not words or len(words) > 3:
            return None
        name = " ".join(words[:2]).title()
        return _run_transaction_query(
            order=pq.get("order"), name=name, date=pq.get("date"),
            date_from=pq.get("date_from"), date_to=pq.get("date_to"),
            types=pq.get("types"), amount_min=pq.get("amount_min"),
            amount_max=pq.get("amount_max"), mode=pq.get("mode"),
        )

    if pq["missing"] == "date":
        date = _extract_date(text)
        date_from, date_to = (None, None)
        if not date:
            date_from, date_to = _extract_date_range(text)
        if not date and not date_from:
            return None
        return _run_transaction_query(
            order=pq.get("order"), name=pq.get("name"), date=date,
            date_from=date_from, date_to=date_to,
            types=pq.get("types"), amount_min=pq.get("amount_min"),
            amount_max=pq.get("amount_max"), mode=pq.get("mode"),
        )

    return None


def _handle_transaction_query(message: str):

    pending_key = _pending_key(_get_current_username())

    text = _normalize(message)
    mentions_transaction = bool(TRANSACTION_WORD_RE.search(text))
    has_date_trigger = any(t in text for t in DATE_TRANSACTION_TRIGGERS)
    has_name_trigger = any(t in text for t in NAME_TRANSACTION_TRIGGERS)

    txn_types = _detect_type(text)
    order = _detect_extremum(text, has_type=bool(txn_types))
    name = _detect_name(text)
    date = _extract_date(text) if (mentions_transaction or has_date_trigger) else None
    date_from, date_to = _extract_date_range(text)

    amount_min, amount_max = _extract_amount_range(text)
    has_amount_range = amount_min is not None or amount_max is not None

    has_query_verb = any(v in text for v in QUERY_VERBS)

    # A bare type keyword ("deposit", "withdraw", "transfer") only counts
    # as a lookup request if there's also an explicit query signal --
    # otherwise "I want to deposit money" would get hijacked away from
    # the normal deposit-action intent.
    type_is_lookup = bool(txn_types) and (
        mentions_transaction or has_date_trigger or has_name_trigger
        or has_query_verb or date_from or date_to or has_amount_range
    )

    mode = _detect_aggregate_mode(text)
    has_extra_filter = bool(
        txn_types or date_from or date_to or has_amount_range or name or date
    )
    # Don't let a bare "how much did i spend" / "total" (no extra filter)
    # hijack the existing 30-day spending-summary handler -- only claim
    # "sum" here when there's a specific filter attached to it.
    if mode == "sum" and not has_extra_filter:
        mode = None

    signals_present = any([
        order, name, date, date_from, date_to, mode, has_amount_range,
        mentions_transaction, has_date_trigger, has_name_trigger, type_is_lookup
    ])

    if not signals_present:
        return None

    if has_date_trigger and date is None and date_from is None and order is None and name is None:
        _pending_query[pending_key] = {
            "missing": "date", "order": order, "types": txn_types,
            "name": name, "amount_min": amount_min, "amount_max": amount_max,
            "mode": mode,
        }
        return _reply(
            "I can look up transactions for a specific date — "
            "try something like \"transactions on 2024-05-01\" "
            "or \"transactions on 10 aug 2026\"."
        )

    if has_name_trigger and name is None and order is None and date is None and date_from is None:
        _pending_query[pending_key] = {
            "missing": "name", "order": order, "types": txn_types,
            "date": date, "date_from": date_from, "date_to": date_to,
            "amount_min": amount_min, "amount_max": amount_max, "mode": mode,
        }
        return _reply(
            "Who would you like to look up transactions for? "
            "Try something like \"transactions with Priya\"."
        )

    result = _run_transaction_query(
        order=order, name=name, date=date, date_from=date_from, date_to=date_to,
        types=txn_types, amount_min=amount_min, amount_max=amount_max, mode=mode,
    )

    # Just mentions "transaction(s)" with no specifics -- let the normal
    # "transactions" intent handle the recent-5 list.
    return result


# ============================================================
# Loan status
# ============================================================

def _get_all_loans(user_id):
    conn = sqlite3.connect("bank.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT loan_type, amount, duration, interest, status, remarks, applied_date
        FROM loans
        WHERE user_id=?
        ORDER BY id DESC
        """,
        (user_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def _calc_emi(amount, duration, interest):
    monthly_rate = interest / 12 / 100
    if monthly_rate > 0:
        return amount * monthly_rate * (1 + monthly_rate) ** duration / ((1 + monthly_rate) ** duration - 1)
    return amount / duration


def _add_months(dt, months):
    """Simple month-add helper (no external dateutil dependency).
    Clamps day to 28 to sidestep month-length edge cases -- fine for an
    estimate, not meant to be exact to the day."""
    total_month_index = dt.month - 1 + months
    year = dt.year + total_month_index // 12
    month = total_month_index % 12 + 1
    day = min(dt.day, 28)
    return dt.replace(year=year, month=month, day=day)


def _handle_loan_query(message: str):

    text = _normalize(message)

    is_list = any(p in text for p in LOAN_LIST_PATTERNS)
    is_due = any(p in text for p in LOAN_DUE_PATTERNS)
    is_owe = any(p in text for p in LOAN_OWE_PATTERNS)
    is_emi = any(p in text for p in LOAN_EMI_PATTERNS)
    is_status = any(p in text for p in LOAN_STATUS_PATTERNS)

    if not any([is_list, is_due, is_owe, is_emi, is_status]):
        return None

    if not session.current_user:
        return _reply("Please log in to check your loan details.")

    user_id = session.current_user[0]
    loans = _get_all_loans(user_id)

    if not loans:
        return _reply(
            "You haven't applied for any loans yet. "
            "Want me to open the Loans page?"
        )

    # --- List all loans ---
    if is_list:
        lines = []
        for loan_type, amount, duration, interest, status, remarks, applied_date in loans:
            emoji = "🟢" if status == "Approved" else ("🔴" if status == "Rejected" else "🟡")
            lines.append(
                f"• {loan_type} — ₹{amount:,.2f} over {duration} months — "
                f"{status} {emoji} (applied {str(applied_date)[:10]})"
            )
        return _reply("📋 Your loans:\n\n" + "\n".join(lines))

    # Everything else works off the most recent loan.
    loan_type, amount, duration, interest, status, remarks, applied_date = loans[0]

    if status != "Approved":
        remark_note = f" — {remarks}" if remarks else ""
        return _reply(
            f"Your most recent loan ({loan_type}, ₹{amount:,.2f}) is currently "
            f"{status}{remark_note}. EMI details apply once a loan is approved."
        )

    emi = _calc_emi(amount, duration, interest)
    total_payable = emi * duration
    total_interest = total_payable - amount

    # --- Next EMI due (estimate only -- no repayment schedule is tracked) ---
    if is_due:
        try:
            applied = datetime.strptime(str(applied_date)[:10], "%Y-%m-%d")
        except (ValueError, TypeError):
            applied = datetime.now()

        now = datetime.now()
        months_elapsed = max(0, (now.year - applied.year) * 12 + (now.month - applied.month))
        next_due = _add_months(applied, months_elapsed + 1)

        return _reply(
            f"📅 Based on your loan start date ({str(applied_date)[:10]}), your next "
            f"estimated EMI of ₹{emi:,.2f} would fall around {next_due.strftime('%Y-%m-%d')}.\n\n"
            f"Note: SmartBank doesn't track individual EMI payments yet, so this is "
            f"an estimate based on a monthly schedule, not a confirmed due date."
        )

    # --- Total owed (estimate only -- assumes no payments made yet) ---
    if is_owe:
        return _reply(
            f"💰 Your {loan_type} of ₹{amount:,.2f} has a total repayable amount of "
            f"₹{total_payable:,.2f} (₹{amount:,.2f} principal + ₹{total_interest:,.2f} interest) "
            f"over {duration} months.\n\n"
            f"Note: SmartBank doesn't yet track individual payments made, so this is "
            f"the full repayment total, not adjusted for anything already paid."
        )

    # --- Just the EMI figure ---
    if is_emi:
        return _reply(
            f"💳 Your estimated monthly EMI for your {loan_type} is "
            f"₹{emi:,.2f} over {duration} months."
        )

    # --- Full status block (original behavior) ---
    status_emoji = "🟢" if status == "Approved" else "🔴"
    reply = (
        f"Your most recent loan application:\n\n"
        f"Type: {loan_type}\n"
        f"Amount: ₹{amount:,.2f}\n"
        f"Duration: {duration} months\n"
        f"Status: {status} {status_emoji}\n"
        f"Remarks: {remarks}\n"
        f"Estimated Monthly EMI: ₹{emi:,.2f}"
    )
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

    if _ollama_ready:
        prompt = (
            "You are Milo, SmartBank's assistant. "
            "Rephrase this raw spending data as a short, "
            "friendly 2-3 sentence summary. Mention the total "
            "and call out the biggest category. "
            "Don't invent numbers not given below.\n\n" + raw_summary
        )
        ollama_reply = _ollama_generate(prompt)
        if ollama_reply:
            reply = ollama_reply

    return _reply(reply)


# ============================================================
# Startup nudges
# ============================================================

def get_startup_nudges():
    return get_nudges()


# ============================================================
# Ollama: intent classification (catches phrasing the rules miss)
# ============================================================

def _ollama_classify_intent(message: str):
    """
    When substring pattern-matching finds no intent, ask the local model
    to pick the closest matching known intent instead of falling
    straight to open-ended free-form chat. This lets phrasing the
    hand-written patterns don't cover -- e.g. "wanna move some cash to
    my buddy" -- still resolve to the right action (transfer) instead of
    dead-ending in generic Q&A. Returns an intent dict from INTENTS, or
    None if Ollama is unavailable or thinks nothing fits well.
    """
    if not _ollama_ready:
        return None

    intent_list = "\n".join(
        f"- {intent['name']}: e.g. \"{intent['patterns'][0]}\", \"{intent['patterns'][-1]}\""
        for intent in INTENTS
    )

    prompt = (
        "You are an intent classifier for Milo, a banking app assistant. "
        "Given the user's message, choose the SINGLE closest matching intent "
        "from the list below, even if the wording doesn't match exactly -- "
        "use your judgement about what the user actually wants to do. "
        "If nothing genuinely fits, respond with exactly: none\n\n"
        f"Intents:\n{intent_list}\n\n"
        f"User message: \"{message}\"\n\n"
        "Respond with ONLY the intent name from the list above, or the word "
        "none. No punctuation, no explanation, nothing else."
    )

    raw = _ollama_generate(prompt)
    if not raw:
        return None
    name = raw.strip().lower().strip(" .\"'")
    return _INTENTS_BY_NAME.get(name)


# ============================================================
# Ollama fallback (open-ended chat, with recent context)
# ============================================================

def _recent_history_snippet(username, max_messages=6):
    """Builds a short "Recent conversation:" block from chat history so
    the Ollama fallback can handle follow-ups like "what about last
    week?" instead of answering each message in isolation."""
    if not username:
        return ""
    try:
        history = chat_history.load_history(username)
    except Exception:
        return ""
    if not history:
        return ""

    recent = history[-max_messages:]
    lines = [
        f"{'User' if entry['role'] == 'user' else 'Milo'}: {entry['text']}"
        for entry in recent
    ]
    return "Recent conversation so far:\n" + "\n".join(lines) + "\n\n"


def _ask_ollama(message: str, username=None):

    if not _ollama_ready:
        return None

    history_snippet = _recent_history_snippet(username)

    prompt = (
        "You are Milo, a friendly and concise AI assistant for SmartBank, "
        "a banking app. Answer the user's question in 2-4 short sentences. "
        "Use the recent conversation below for context if it's relevant to "
        "the current message, e.g. resolving follow-ups like \"what about "
        "last week\". Do not give specific financial or investment advice. "
        "For banking actions such as deposit, withdraw, transfer, and loans, "
        "direct the user to the appropriate SmartBank page.\n\n"
        f"{history_snippet}"
        f"User's message: {message}"
    )

    return _ollama_generate(prompt)


_FALLBACK_HELP_TEXT = (
    "I'm not sure I understood that. "
    "You can ask me about:\n"
    "• Deposits\n"
    "• Withdrawals\n"
    "• Transfers\n"
    "• Loans\n"
    "• Transactions (by type, date, date range, person, or amount)\n"
    "• Spending summary\n"
    "• Smallest / largest transaction\n"
    "• Totals and counts\n"
    "• Banking services\n\n"
    "Try something like \"check my balance\" or \"largest withdrawal this month\"."
)


# ============================================================
# Main assistant
# ============================================================

# Handlers tried in order (before the generic intent list / Ollama
# fallback). Each takes the raw message and returns a result dict or
# None if it doesn't apply. Order matters: transaction queries must be
# checked before loan/spending since some phrasings could overlap.
_QUERY_HANDLERS = (
    _handle_transaction_query,
    _handle_loan_query,
    _handle_spending_summary,
)


def ask_assistant(message: str):

    username = _get_current_username()
    pending_key = _pending_key(username)

    if username:
        chat_history.append_message(username, "user", message)

    text = _normalize(message)

    # --- Yes / No follow-up on a previously offered action ---
    # Scoped per-user via pending_key so one user's confirmation can
    # never trigger or clear a different user's pending action.
    if _last_action.get(pending_key):
        if text in YES_WORDS or any(w in text for w in YES_WORDS):
            action = _last_action[pending_key]
            _last_action[pending_key] = None
            return _finalize(username, _reply("Great, opening that for you now.", action))

        if text in NO_WORDS or any(w in text for w in NO_WORDS):
            _last_action[pending_key] = None
            return _finalize(username, _reply("No problem! Let me know if you need anything else."))

    # --- Slot-filling follow-up on a previously incomplete query ---
    # e.g. bot asked "who would you like to look up?" and this message
    # is the answer ("Priya") rather than a brand-new question.
    pq = _pending_query.get(pending_key)
    if pq:
        resolved = _resolve_pending_query(pq, message)
        _pending_query[pending_key] = None
        if resolved is not None:
            return _finalize(username, resolved)
        # Reply didn't look like an answer to the pending question --
        # fall through and treat this message as brand new.

    # --- Transaction queries / loan status / spending summary ---
    # Checked before generic intents so they aren't swallowed by the
    # broader "transactions" keyword match.
    for handler in _QUERY_HANDLERS:
        result = handler(message)
        if result:
            return _finalize(username, result)

    # --- Normal rule-based intents ---
    intent = _match_intent(message)

    # --- Ollama intent classification ---
    # Only reached if substring patterns found nothing. Catches phrasing
    # variety the hand-written patterns don't cover, before giving up
    # and treating the message as generic open-ended chat.
    if not intent:
        intent = _ollama_classify_intent(message)

    if intent:
        reply = random.choice(intent["replies"])
        if intent["action"]:
            _last_action[pending_key] = intent["action"]
            reply += "\n\nWould you like me to open that for you? (yes/no)"
        return _finalize(username, _reply(reply))

    # --- Ollama fallback (open-ended, with recent context) ---
    _last_action[pending_key] = None
    ollama_reply = _ask_ollama(message, username)
    return _finalize(username, _reply(ollama_reply or _FALLBACK_HELP_TEXT))