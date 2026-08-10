"""
security.py

Simple password check for SmartBank AI (no hashing, no lockout).
"""


def verify_password(stored_password, provided_password: str) -> bool:
    if stored_password is None:
        return False
    return stored_password == provided_password