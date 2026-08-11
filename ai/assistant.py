import re
import random
import os
import sqlite3

import session
from ai import chat_history
from ai.banking_ai import get_spending_summary, get_nudges

# =========================
# Gemini setup (optional — degrades gracefully if not configured)
# =========================
_gemini_ready = False
_gemini_client = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — GEMINI_API_KEY must be a real env var instead

try:
    from google import genai

    _api_key = os.getenv("GEMINI_API_KEY")

    if _api_key:
        _gemini_client = genai.Client(api_key=_api_key)
        _gemini_ready = True

except ImportError:
    pass  # google-genai not installed — Gemini fallback simply won't run


# =========================
# Rule-based intents
# =========================
INTENTS = [
    {
        "name": "greeting",
        "patterns": ["hi", "hello", "hey", "good morning", "good afternoon",
                     "good evening", "yo", "sup", "hiya"],
        "replies": [
            "Hello! I'm Milo, your SmartBank AI Assistant. How can I help you today?",
            "Hey there! What can I do for you today?",
            "Hi! Ask me about deposits, withdrawals, transfers, loans, or your balance."
        ],
        "action": None,
    },
    {
        "name": "balance",
        "patterns": ["balance", "bank balance", "account balance", "how much money",
                     "how much do i have", "check balance", "my balance"],
        "replies": [
            "Sure! I can show your account balance on the Dashboard.",
            "You can view your current balance from the Dashboard page.",
        ],
        "action": "balance",
    },
    {
        "name": "deposit",
        "patterns": ["deposit", "add money", "put money", "add funds",
                     "deposit money", "make a deposit"],
        "replies": [
            "I can help you make a deposit. Want me to open the Deposit page?",
            "Sure, let's get that deposit sorted. Opening the Deposit page.",
        ],
        "action": "deposit",
    },
    {
        "name": "withdraw",
        "patterns": ["withdraw", "withdrawal", "take out money", "cash out",
                     "withdraw money", "get cash"],
        "replies": [
            "I can help you withdraw funds. Want me to open the Withdraw page?",
            "Let's process that withdrawal — opening the Withdraw page.",
        ],
        "action": "withdraw",
    },
    {
        "name": "transfer",
        "patterns": ["transfer", "send money", "move money", "transfer funds",
                     "send funds", "pay someone", "wire money"],
        "replies": [
            "I can help you transfer money. Want me to open the Transfer page?",
            "Sure, let's set up that transfer. Opening the Transfer page.",
        ],
        "action": "transfer",
    },
    {
        "name": "loan",
        "patterns": ["apply for loan", "apply loan", "need a loan", "new loan",
                     "take a loan", "borrow money"],
        "replies": [
            "I can help with a new loan application. Want me to open the Loans page?",
            "Let's take a look at your loan options — opening the Loans page.",
        ],
        "action": "loan",
    },
    {
        "name": "transactions",
        "patterns": ["transactions", "transaction history", "recent transactions",
                     "spending history", "statement", "activity"],
        "replies": [
            "I can pull up your recent transactions. Want me to open that page?",
            "Sure, let's review your transaction history.",
        ],
        "action": "transactions",
    },
    {
        "name": "documents_needed",
        "patterns": ["documents needed", "what documents", "documents required",
                     "documents for loan", "id proof"],
        "replies": [
            "For a loan application you'll need to upload three documents: "
            "an ID Proof (like Aadhaar), an Income Proof, and a Bank Statement. "
            "You can upload these directly on the Loans page."
        ],
        "action": None,
    },
    {
        "name": "interest_rate",
        "patterns": ["interest rate", "what is the interest", "loan interest",
                     "how much interest"],
        "replies": [
            "SmartBank currently offers loans at a flat 8.5% annual interest rate. "
            "You can see an estimated EMI on the Loans page as you enter an amount and duration."
        ],
        "action": None,
    },
    {
        "name": "security",
        "patterns": ["is my money safe", "is this secure", "security", "safe to use",
                     "data privacy", "is smartbank safe"],
        "replies": [
            "Your account is protected with password-based authentication, and all "
            "transactions are logged for your review on the Transactions page. "
            "If anything looks unfamiliar, contact support right away."
        ],
        "action": None,
    },
    {
        "name": "close_account",
        "patterns": ["close my account", "close account", "delete my account",
                     "delete account", "deactivate account"],
        "replies": [
            "Closing an account isn't something I can do directly from chat, for "
            "your security. Please contact SmartBank support or visit a branch, "
            "and an administrator will help you close your account safely."
        ],
        "action": None,
    },
    {
        "name": "contact_support",
        "patterns": ["contact support", "customer support", "help desk",
                     "talk to a human", "speak to someone"],
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
            "• Loans (apply, check status, EMI info)\n"
            "• Transactions\n"
            "• Checking your balance\n"
            "• Your spending summary\n"
            "• General questions — just ask!\n\n"
            "What would you like to do?"
        ],
        "action": None,
    },
]

# Checked BEFORE the generic intent loop, since it needs a DB lookup
# rather than a static reply.
LOAN_STATUS_PATTERNS = ["loan status", "my loan", "status of my loan",
                         "loan application status", "check my loan"]

SPENDING_PATTERNS = ["how much did i spend", "spending this month", "spending summary",
                      "how much have i spent", "my spending", "spent this month"]

YES_WORDS = {"yes", "yeah", "yep", "sure", "ok", "okay", "please", "go ahead"}
NO_WORDS = {"no", "nope", "nah", "not now", "cancel"}

_last_action = {"pending": None}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _match_intent(message: str):
    text = _normalize(message)
    best_intent = None
    best_score = 0

    for intent in INTENTS:
        for pattern in intent["patterns"]:
            if pattern in text:
                score = len(pattern)
                if score > best_score:
                    best_score = score
                    best_intent = intent

    return best_intent


def _get_current_username():
    try:
        return session.current_user[2]  # (id, name, username, password, balance, email)
    except (TypeError, IndexError):
        return None


# =========================
# Loan status lookup (DB-aware, personalized)
# =========================
def _handle_loan_status(message: str):
    text = _normalize(message)

    if not any(p in text for p in LOAN_STATUS_PATTERNS):
        return None

    if not session.current_user:
        return {"reply": "Please log in to check your loan status.", "action": None}

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
        return {
            "reply": "You haven't applied for any loans yet. Want me to open the Loans page?",
            "action": None
        }

    loan_type, amount, duration, interest, status, remarks = loan

    monthly_rate = interest / 12 / 100
    if monthly_rate > 0:
        emi = amount * monthly_rate * (1 + monthly_rate) ** duration / \
              ((1 + monthly_rate) ** duration - 1)
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

    return {"reply": reply, "action": None}


# =========================
# Spending summary (DB-aware, Gemini-paraphrased)
# =========================
def _handle_spending_summary(message: str):
    text = _normalize(message)

    if not any(p in text for p in SPENDING_PATTERNS):
        return None

    if not session.current_user:
        return {"reply": "Please log in to see your spending summary.", "action": None}

    summary = get_spending_summary(days=30)

    if not summary:
        return {
            "reply": "You haven't made any outgoing transactions in the last 30 days.",
            "action": None
        }

    breakdown_lines = "\n".join(
        f"- {t}: ₹{amt:,.2f}" for t, amt in summary["breakdown"].items()
    )
    raw_summary = (
        f"Total spent in the last 30 days: ₹{summary['total']:,.2f} "
        f"across {summary['count']} transactions.\n{breakdown_lines}"
    )

    reply = raw_summary

    if _gemini_ready:
        try:
            prompt = (
                "You are Milo, SmartBank's assistant. Rephrase this raw spending "
                "data as a short, friendly 2-3 sentence summary. Mention the total "
                "and call out the biggest category. Don't invent numbers not given "
                "below.\n\n" + raw_summary
            )
            response = _gemini_client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt
            )
            if response and response.text:
                reply = response.text.strip()
        except Exception:
            pass  # fall back to raw_summary, already set above

    return {"reply": reply, "action": None}


# =========================
# Startup nudges (called by the UI on chat page load, not from ask_assistant)
# =========================
def get_startup_nudges():
    return get_nudges()


# =========================
# Gemini fallback
# =========================
def _ask_gemini(message: str):
    if not _gemini_ready:
        return None

    try:
        prompt = (
            "You are Milo, a friendly and concise AI assistant for SmartBank, "
            "a banking app. Answer the user's question in 2-4 short sentences. "
            "Do not give specific financial or investment advice — for banking "
            "actions (deposit, withdraw, transfer, loans), direct them to ask "
            "you to do that action instead. "
            f"User's message: {message}"
        )

        response = _gemini_client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        return response.text.strip() if response and response.text else None

    except Exception:
        return None  # network issue, bad key, quota, etc. — fall back gracefully


# =========================
# Main entry point
# =========================
def ask_assistant(message: str) -> dict:

    username = _get_current_username()
    if username:
        chat_history.append_message(username, "user", message)

    text = _normalize(message)

    # Yes/No follow-up to a pending suggested action
    if _last_action["pending"]:
        if text in YES_WORDS or any(w in text for w in YES_WORDS):
            action = _last_action["pending"]
            _last_action["pending"] = None
            result = {"reply": "Great, opening that for you now.", "action": action}
            if username:
                chat_history.append_message(username, "milo", result["reply"])
            return result

        if text in NO_WORDS or any(w in text for w in NO_WORDS):
            _last_action["pending"] = None
            result = {"reply": "No problem! Let me know if you need anything else.", "action": None}
            if username:
                chat_history.append_message(username, "milo", result["reply"])
            return result

    # Loan status — needs a DB lookup, checked before generic intents
    loan_status_result = _handle_loan_status(message)
    if loan_status_result:
        if username:
            chat_history.append_message(username, "milo", loan_status_result["reply"])
        return loan_status_result

    # Spending summary — also needs a DB lookup + Gemini paraphrase
    spending_result = _handle_spending_summary(message)
    if spending_result:
        if username:
            chat_history.append_message(username, "milo", spending_result["reply"])
        return spending_result

    # Rule-based intents
    intent = _match_intent(message)

    if intent:
        reply = random.choice(intent["replies"])

        if intent["action"]:
            _last_action["pending"] = intent["action"]
            reply += "\n\nWould you like me to open that for you? (yes/no)"
            result = {"reply": reply, "action": None}
        else:
            result = {"reply": reply, "action": None}

        if username:
            chat_history.append_message(username, "milo", result["reply"])
        return result

    # Nothing rule-based matched — try Gemini
    _last_action["pending"] = None
    gemini_reply = _ask_gemini(message)

    if gemini_reply:
        result = {"reply": gemini_reply, "action": None}
    else:
        result = {
            "reply": (
                "I'm not sure I understood that. You can ask me about:\n"
                "• Deposits\n"
                "• Withdrawals\n"
                "• Transfers\n"
                "• Loans (apply, check status)\n"
                "• Transactions\n"
                "• Spending summary\n"
                "• Banking services\n\n"
                "Try something like \"check my balance\" or \"what's my loan status\"."
            ),
            "action": None
        }

    if username:
        chat_history.append_message(username, "milo", result["reply"])

    return result
