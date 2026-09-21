"""
core/text_utils.py
==================
ছোট ছোট text helper (SS27 + Label V3 এ একই ছিল)।
"""
import re


def strip_leading_number(text: str) -> str:
    """শুরুতে "4." / "12." এর মতো digit + dot থাকলে বাদ দেয়।"""
    return re.sub(r'^\d+\.\s*', '', text or "").strip()


def clean_item_name_english(name: str, prefixes=()) -> str:
    """
    Item_name_EN থেকে শুরুর number আর prefix বাদ দিয়ে CAPITAL LETTERS এ ফেরত দেয়।

    prefixes: config.ITEM_NAME_PREFIXES_SS27 / ITEM_NAME_PREFIXES_V3
              (case-insensitive; লম্বা phrase আগে বসাতে হবে)
    """
    if not isinstance(name, str):
        return ""

    text = strip_leading_number(name.strip())
    lower = text.lower()

    for p in prefixes:
        p = p.lower()
        if lower.startswith(p):
            text = text[len(p):].strip(" -_,./").strip()
            break

    return text.upper()
