"""
ai/chat_history.py

Persists each user's chatbot conversation to a local JSON file, so
Milo "remembers" what was said in previous sessions instead of
resetting every time the Chatbot page is opened.

Storage: chat_history/{username}.json — a simple list of messages,
capped at MAX_MESSAGES to keep files small.

No database changes needed — this is entirely separate from bank.db.
"""

import os
import json
from datetime import datetime

CHAT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chat_history")
MAX_MESSAGES = 100  # keep files from growing unbounded


def _safe_username(username: str) -> str:
    """Strip anything that isn't filesystem-safe from the username."""
    return "".join(c for c in str(username) if c.isalnum() or c in ("-", "_")) or "unknown_user"


def _get_path(username: str) -> str:
    os.makedirs(CHAT_DIR, exist_ok=True)
    return os.path.join(CHAT_DIR, f"{_safe_username(username)}.json")


def load_history(username: str) -> list:
    """
    Returns a list of {"role": "user"|"milo", "text": str, "time": str}
    dicts, oldest first. Returns [] if no history exists yet.
    """
    path = _get_path(username)

    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def append_message(username: str, role: str, text: str):
    """
    Appends one message to the user's history and saves it.
    role should be "user" or "milo".
    """
    history = load_history(username)

    history.append({
        "role": role,
        "text": text,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Trim from the front if too long
    if len(history) > MAX_MESSAGES:
        history = history[-MAX_MESSAGES:]

    path = _get_path(username)

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except OSError:
        pass  # non-critical — chat still works, just won't persist this turn


def clear_history(username: str):
    """Optional helper if you ever want a 'Clear Chat' button."""
    path = _get_path(username)
    if os.path.exists(path):
        os.remove(path)