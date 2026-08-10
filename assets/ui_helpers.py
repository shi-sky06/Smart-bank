"""
assets/ui_helpers.py

Shared, reusable UI building blocks so every page in SmartBank AI
(Deposit, Withdraw, Transfer, Loan, Transactions, Login, Register, etc.)
can look consistent without copy-pasting layout code everywhere.

Two main pieces:

1. build_hero_header(...)
   A colored banner with the SmartBank logo + a title/subtitle,
   for the top of a page. Pick a different `accent_color` per page
   type (e.g. green for Deposit, red for Withdraw, blue for Transfer)
   so each page still feels distinct.

2. build_color_strip(...)
   A thin colored bar (used at the top of cards, same visual language
   as the Dashboard's stat cards) to add quick color-coding anywhere.

Usage example (inside any page's __init__, after creating `container`):

    from assets.ui_helpers import build_hero_header, PAGE_COLORS

    build_hero_header(
        container,
        title="Deposit Money",
        subtitle="Add funds to your account instantly",
        icon_name="money_bag",
        accent_color=PAGE_COLORS["deposit"]
    )
"""

import customtkinter as ctk
from assets.icon_loader import get_icon


# Suggested accent color per page — reuse these so colors stay
# consistent with the Dashboard cards you already have.
PAGE_COLORS = {
    "login": "#1E3A8A",         # navy (brand)
    "register": "#1E3A8A",      # navy (brand)
    "dashboard": "#1E3A8A",     # navy (brand)
    "deposit": "#16A34A",       # green
    "withdraw": "#DC2626",      # red
    "transfer": "#2563EB",      # blue
    "transactions": "#2563EB",  # blue
    "loan": "#9333EA",          # purple
    "chatbot": "#9333EA",       # purple
}

PAGE_ICONS = {
    "login": "bank_logo",
    "register": "bank_logo",
    "dashboard": "bank_logo",
    "deposit": "money_bag",
    "withdraw": "down_arrow",
    "transfer": "repeat",
    "transactions": "scroll",
    "loan": "credit_card",
    "chatbot": "robot",
}


def build_hero_header(parent, title, subtitle=None, icon_name="bank_logo",
                       accent_color="#1E3A8A", icon_size=48, height=110):
    """
    Colored banner with logo/icon + title + optional subtitle.
    Returns the outer frame in case the caller wants to pack more
    below/around it.
    """
    hero = ctk.CTkFrame(parent, corner_radius=18, fg_color=accent_color, height=height)
    hero.pack(fill="x", pady=(0, 20))
    hero.pack_propagate(False)

    content = ctk.CTkFrame(hero, fg_color="transparent")
    content.pack(expand=True, fill="both", padx=25, pady=15)

    icon_img = get_icon(icon_name, size=icon_size)
    if icon_img:
        ctk.CTkLabel(content, image=icon_img, text="").pack(side="left", padx=(0, 18))

    text_col = ctk.CTkFrame(content, fg_color="transparent")
    text_col.pack(side="left", fill="both", expand=True)

    ctk.CTkLabel(
        text_col, text=title, font=("Arial", 22, "bold"), text_color="white"
    ).pack(anchor="w")

    if subtitle:
        ctk.CTkLabel(
            text_col, text=subtitle, font=("Arial", 13), text_color="#E5EAF5"
        ).pack(anchor="w", pady=(2, 0))

    return hero


def build_color_strip(parent, color, height=6):
    """
    Thin colored bar — drop at the top of any CTkFrame/card to
    color-code it (matches the Dashboard stat card stripes).
    """
    strip = ctk.CTkFrame(parent, height=height, corner_radius=0, fg_color=color)
    strip.pack(fill="x", side="top")
    return strip


def build_icon_badge(parent, icon_name, accent_bg, size=28, badge_size=52):
    """
    Circular colored badge with a centered icon image, same style
    as the Dashboard stat cards. Returns the badge frame.
    """
    badge = ctk.CTkFrame(
        parent, width=badge_size, height=badge_size,
        corner_radius=badge_size // 2, fg_color=accent_bg
    )
    badge.pack_propagate(False)

    icon_img = get_icon(icon_name, size=size)
    if icon_img:
        ctk.CTkLabel(badge, image=icon_img, text="").place(relx=0.5, rely=0.5, anchor="center")

    return badge
