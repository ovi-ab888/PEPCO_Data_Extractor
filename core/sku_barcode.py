"""
core/sku_barcode.py
===================
SKU (8-digit) আর Barcode (13-digit)। দুটো একই loop-এ, একই নিয়মে বের হয় এবং
সবসময় জোড়ায় (zip) ব্যবহার হয়, তাই এক file-এ।

  extract_skus_and_barcodes()  SS27 + Care
  extract_skus()               Label V3 (barcode অন্যভাবে, page 4+ থেকে)
  build_colour_sku()           "PINK • SKU 12345678"
  join_skus_for_filename()     "12345678_87654321"
"""
import re

import streamlit as st

from core.pdf_utils import dedupe


def extract_skus_and_barcodes(pages_text):
    """
    8-digit SKU আর 13-digit barcode বের করে (SS27 + Care)।
    "barcode: xxxxxxxxxxxxx" লেখা barcode গুলো বাদ যায়।
    SKU আর barcode-এর সংখ্যা না মিললে ছোটটার সমান পর্যন্ত নেয় (warning সহ)।
    Return: (skus, barcodes) — না পেলে error দেখিয়ে (None, None)।
    """
    skus, barcodes, excluded = [], [], set()

    for txt in pages_text:
        skus.extend(re.findall(r"\b\d{8}\b", txt))
        barcodes.extend(re.findall(r"\b\d{13}\b", txt))
        excluded.update(re.findall(r"barcode:\s*(\d{13})", txt))

    skus = dedupe(skus)
    barcodes = dedupe(barcodes)
    valid_barcodes = [b for b in barcodes if b not in excluded]

    if not skus or not valid_barcodes:
        st.error("SKU or Barcode missing.")
        return None, None

    if len(skus) != len(valid_barcodes):
        min_len = min(len(skus), len(valid_barcodes))
        st.warning(
            f"SKU ({len(skus)}) and Barcode ({len(valid_barcodes)}) differ. Using first {min_len}."
        )
        skus = skus[:min_len]
        valid_barcodes = valid_barcodes[:min_len]

    return skus, valid_barcodes


def extract_skus(pages_text):
    """শুধু 8-digit SKU (Label V3)। না পেলে error দেখিয়ে None।"""
    skus = []
    for txt in pages_text:
        skus.extend(re.findall(r"\b\d{8}\b", txt))
    skus = dedupe(skus)

    if not skus:
        st.error("SKU missing from PDF.")
        return None
    return skus


def build_colour_sku(colour, sku):
    """SS27-এর Colour_SKU column: "PINK • SKU 12345678"।"""
    return f"{colour} • SKU {sku}"


def join_skus_for_filename(skus):
    """CSV file নামের জন্য SKU গুলো "_" দিয়ে জোড়া; না থাকলে "UNKNOWN"।"""
    return "_".join(skus) if skus else "UNKNOWN"
