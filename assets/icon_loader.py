"""
assets/icon_loader.py

Small shared helper for loading the PNG icon set as CTkImage objects,
so every page in the app can use the same colorful icons consistently
instead of relying on emoji font rendering (which looks inconsistent
across Windows/Mac/Linux).

Usage:
    from assets.icon_loader import get_icon
    icon = get_icon("bank", size=32)
    ctk.CTkLabel(parent, image=icon, text="").pack()
"""

import os
from PIL import Image
import customtkinter as ctk

_ICON_DIR = os.path.join(os.path.dirname(__file__), "icons")
_cache = {}


def get_icon(name: str, size: int = 32):
    """
    Returns a CTkImage for the given icon name (without .png extension),
    e.g. get_icon("bank"), get_icon("robot", size=48).

    Falls back to None if the file is missing, so callers can gracefully
    fall back to an emoji/text label instead of crashing.
    """
    cache_key = (name, size)
    if cache_key in _cache:
        return _cache[cache_key]

    path = os.path.join(_ICON_DIR, f"{name}.png")

    if not os.path.exists(path):
        return None

    pil_image = Image.open(path)
    ctk_image = ctk.CTkImage(
        light_image=pil_image,
        dark_image=pil_image,
        size=(size, size)
    )

    _cache[cache_key] = ctk_image
    return ctk_image
