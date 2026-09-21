"""
core/collection.py
==================
Collection বের করা + COLLECTION_MAPPING প্রয়োগ + Boys/Girls suffix (SS27 / app 1-এর logic)।

Flow:  extract_collection()  ->  modify_collection()
"""
import re

import streamlit as st

from core.classification import get_classification_type
from core.config import COLLECTION_MAPPING


def extract_collection_value(raw_text):
    """
    Format: TYPE - NAME - SEASON - CODE
    প্রথম অংশ (TYPE) skip করে, SEASON (SS27, AW26) ও CODE (শুধু digit) বাদ দিয়ে
    যা প্রথমে থাকে সেটাই NAME। কিছু না পেলে "UNKNOWN"।
    """
    parts = [p.strip() for p in raw_text.split("-") if p.strip()]
    if not parts:
        return "UNKNOWN"

    parts = parts[1:]  # প্রথম অংশ (TYPE) skip

    for p in parts:
        if re.fullmatch(r"[A-Za-z]{2}\d{2}", p):  # SEASON skip
            continue
        if p.isdigit():                            # CODE skip
            continue
        return p

    return "UNKNOWN"


def map_collection(collection_value, item_class):
    """
    Item classification অনুযায়ী COLLECTION_MAPPING থেকে নতুন নাম বসায়
    (যেমন FUNDAY CLUB -> COLLECTION_1)। mapping না মিললে আগের নামই থাকে।
    """
    class_type = get_classification_type(item_class)
    if class_type and class_type in COLLECTION_MAPPING:
        for orig, new in COLLECTION_MAPPING[class_type].items():
            if orig.upper() in collection_value.upper():
                return new
    return collection_value


def extract_collection(pages_text, item_class, manual_key="manual_collection_input"):
    """
    page 1 থেকে Collection বের করে, না পেলে manual input চায়,
    তারপর COLLECTION_MAPPING প্রয়োগ করে।
    manual_key: প্রতি mode-এ আলাদা দিন — widget key clash এড়াতে।
    """
    m = re.search(r"Collection\s*\.{2,}\s*(.+)", pages_text[0])
    value = extract_collection_value(m.group(1)) if m else "UNKNOWN"

    if not value or value == "UNKNOWN":
        st.warning("⚠️ Collection not found in PDF. Enter Collection manually:")
        manual = st.text_input("Collection (e.g. MODERN 1):", key=manual_key)
        if manual and manual.strip():
            value = manual.strip().upper()

    return map_collection(value, item_class)


def modify_collection(collection, item_class):
    """Boys হলে " B", Girls হলে " G" শেষে যোগ করে।"""
    if not item_class:
        return collection

    ic = item_class.lower()

    if any(x in ic for x in ['younger boys', 'older boys']):
        return f"{collection} B"
    if any(x in ic for x in ['younger girls', 'older girls']):
        return f"{collection} G"

    return collection
