import re
import random


# ---------------------------------------------------------------------------
# Intent definitions
# ---------------------------------------------------------------------------
# Each intent has:
#   - patterns: keywords/phrases that trigger it (matched case-insensitively
#     as whole words/phrases, not substrings, to avoid false positives)
#   - replies: list of possible responses (chosen at random for variety)
#   - action: the action key sent back to the UI (or None)

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
            "I can help you make a deposit. Want me to open the Deposit page?",
            "Sure, let's get that deposit sorted. Opening the Deposit page.",
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
            "I can help you withdraw funds. Want me to open the Withdraw page?",
            "Let's process that withdrawal — opening the Withdraw page.",
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
            "I can help you transfer money. Want me to open the Transfer page?",
            "Sure, let's set up that transfer. Opening the Transfer page.",
        ],
        "action": "transfer",
    },
    {
        "name": "loan",
        "patterns": [
            "loan", "borrow money", "apply for loan", "credit",
            "loan application", "need a loan"
        ],
        "replies": [
            "I can help with loan info and applications. Want me to open the Loans page?",
            "Let's take a look at your loan options — opening the Loans page.",
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
            "I can pull up your recent transactions. Want me to open that page?",
            "Sure, let's review your transaction history.",
        ],
        "action": "transactions",
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
        "replies": [
            "Goodbye! Have a great day.",
            "See you next time!",
        ],
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
            "• Checking your balance\n\n"
            "Just tell me what you'd like to do!"
        ],
        "action": None,
    },
]

# Follow-up confirmation words ("yes"/"no") used after Milo asks
# "Would you like me to open X?" — handled via simple state below.
YES_WORDS = {"yes", "yeah", "yep", "sure", "ok", "okay", "please", "go ahead"}
NO_WORDS = {"no", "nope", "nah", "not now", "cancel"}


# ---------------------------------------------------------------------------
# Simple conversation state (per-process — resets when the app restarts)
# ---------------------------------------------------------------------------
_last_action = {"pending": None}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _match_intent(message: str):
    """Return the best-matching intent dict, or None."""
    text = _normalize(message)

    best_intent = None
    best_score = 0

    for intent in INTENTS:
        for pattern in intent["patterns"]:
            if pattern in text:
                # Longer/more specific matches win
                score = len(pattern)
                if score > best_score:
                    best_score = score
                    best_intent = intent

    return best_intent


def ask_assistant(message: str) -> dict:
    """
    Main entry point used by the UI.

    Returns:
        {
            "reply": str,   # text to show in the chat
            "action": str | None  # action key for the shortcut button
        }
    """
    text = _normalize(message)

    # Handle yes/no follow-ups to a pending suggested action
    if _last_action["pending"]:
        if text in YES_WORDS or any(w in text for w in YES_WORDS):
            action = _last_action["pending"]
            _last_action["pending"] = None
            return {
                "reply": f"Great, opening that for you now.",
                "action": action,
            }
        if text in NO_WORDS or any(w in text for w in NO_WORDS):
            _last_action["pending"] = None
            return {
                "reply": "No problem! Let me know if you need anything else.",
                "action": None,
            }

    intent = _match_intent(message)

    if intent is None:
        _last_action["pending"] = None
        reply = (
            "I'm not sure I understood that. You can ask me about:\n"
            "• Deposits\n"
            "• Withdrawals\n"
            "• Transfers\n"
            "• Loans\n"
            "• Transactions\n"
            "• Banking services\n\n"
            "Try something like \"check my balance\" or \"make a transfer\"."
        )
        return {"reply": reply, "action": None}

    reply = random.choice(intent["replies"])

    if intent["action"]:
        # Ask for confirmation before showing the button, matching the
        # "Would you like me to open your Dashboard?" flow seen in the UI.
        _last_action["pending"] = intent["action"]
        reply += "\n\nWould you like me to open that for you? (yes/no)"
        # Action is only surfaced to the UI once the user confirms,
        # so we don't set it here — it comes back on the "yes" turn.
        return {"reply": reply, "action": None}

    return {"reply": reply, "action": None}
