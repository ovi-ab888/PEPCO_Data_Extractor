"""
core/inner_outer.py
===================
Label V3 (Inner / Outer sticker) এর সব extraction function ও logic।

  Page 4 এবং তার পর থেকে:
    extract_all_tc_numbers   TC নম্বর (সর্বোচ্চ 7টা, unique)
    extract_all_barcodes     13-digit barcode (সর্বোচ্চ 7টা, unique)
    extract_product_name     Product name
    extract_inner_kg         "MAX. 5 kg"
    extract_season_st        "SS27"
    extract_inner_qty        "12 Pcs"
    extract_outer_qty        "6 Inner"

  Page 1 থেকে:
    extract_pictogram        PIC00033 -> "A"   (PICTOGRAM_MAPPING)
    extract_promotional      PROMO -> "P", KVI -> "K", HS -> "H"   (PROMOTIONAL_MAPPING)

  একসাথে সব:
    extract_inner_outer_fields()   ওপরের সব field + TC_Number_st1..7 + Barcode_st1..7
    tc_barcode_columns()           TC / Barcode column-এর নামের list

Page 1, 2, 3 থেকে TC/barcode/product/kg/season/qty নেওয়া হয় না
(V3_START_PAGE_INDEX = 3, কারণ index 0-based)।
"""
import re

from core.config import (
    PICTOGRAM_MAPPING,
    PROMOTIONAL_MAPPING,
    V3_MAX_ITEMS,
    V3_START_PAGE_INDEX,
)


def _pages_4_plus(pages_text):
    """Page 4 থেকে শেষ পর্যন্ত। PDF-এ ৪ page-এর কম হলে খালি list।"""
    return pages_text[V3_START_PAGE_INDEX:]


# ================================================================
#  PAGE 4+ FIELDS
# ================================================================
def extract_all_tc_numbers(pages_text):
    """সব TC নম্বর ("T1234")। Page 4+ থেকে, unique, সর্বোচ্চ 7টা।"""
    patterns = [
        r"TC\s*-\s*(T\d+)",
        r"TC\s*[:.]?\s*(T\d+)",
    ]

    tc_list = []
    for page_text in _pages_4_plus(pages_text):
        for pattern in patterns:
            for m in re.findall(pattern, page_text, re.IGNORECASE):
                if m not in tc_list:
                    tc_list.append(m)

    return tc_list[:V3_MAX_ITEMS]


def extract_all_barcodes(pages_text):
    """সব 13-digit barcode। Page 4+ থেকে, unique (order ঠিক রেখে), সর্বোচ্চ 7টা।"""
    barcode_list = []
    for page_text in _pages_4_plus(pages_text):
        barcode_list.extend(re.findall(r"\b\d{13}\b", page_text))

    unique_barcodes = []
    for b in barcode_list:
        if b not in unique_barcodes:
            unique_barcodes.append(b)

    return unique_barcodes[:V3_MAX_ITEMS]


def extract_product_name(pages_text):
    """Product name। Page 4+ থেকে প্রথমটা; না পেলে ""।"""
    for text in _pages_4_plus(pages_text):
        m = re.search(r"ITEM\s*\d+\s*\n\s*(.+)", text, re.IGNORECASE)
        if not m:
            m = re.search(r"Product\s*name\s*[:.]?\s*(.+)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def extract_inner_kg(pages_text):
    """Inner-এর ওজন: "MAX. 5 kg"। Page 4+ থেকে; না পেলে ""।"""
    for text in _pages_4_plus(pages_text):
        m = re.search(r"MAX\.?\s*(\d+)\s*kg", text, re.IGNORECASE)
        if not m:
            m = re.search(r"(\d+)\s*kg", text, re.IGNORECASE)
        if m:
            return f"MAX. {m.group(1)} kg"
    return ""


def extract_season_st(pages_text):
    """Season code ("SS27", "AW26"...)। Page 4+ থেকে; না পেলে ""।"""
    for text in _pages_4_plus(pages_text):
        m = re.search(r"\b(AW|SS|FW|SW)\d{2}\b", text, re.IGNORECASE)
        if m:
            return m.group(0).upper()
    return ""


def extract_inner_qty(pages_text):
    """Inner quantity: "12 Pcs"। Page 4+ থেকে; না পেলে ""।"""
    for text in _pages_4_plus(pages_text):
        m = re.search(r"(\d+)\s*Pcs", text, re.IGNORECASE)
        if m:
            return f"{m.group(1)} Pcs"
    return ""


def extract_outer_qty(pages_text):
    """Outer quantity: "6 Inner"। Page 4+ থেকে; না পেলে ""।"""
    patterns = [
        r"(\d+)\s*Inner\s*OUTER",
        r"(\d+)\s*OUTER",
        r"OUTER\s*[:.]?\s*(\d+)",
        r"(\d+)\s*X\s*INNER\s*OUTER",
        r"OUTER\s*QTY\s*[:.]?\s*(\d+)",
    ]
    for text in _pages_4_plus(pages_text):
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return f"{m.group(1)} Inner"
    return ""


# ================================================================
#  PAGE 1 FIELDS
# ================================================================
def extract_pictogram(pages_text):
    """
    Page 1-এর "Pictogram no ... PIC00033" -> PICTOGRAM_MAPPING-এর অক্ষর/সংখ্যা ("A")।
    না পেলে বা mapping-এ না থাকলে ""।
    """
    m = re.search(
        r"Pictogram\s*no.*?(PIC\d{5})",
        pages_text[0],
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        return PICTOGRAM_MAPPING.get(m.group(1).upper(), "")
    return ""


def extract_promotional(pages_text):
    """
    Page 1-এর "Promotional product ... PROMO/KVI/HS/NON PROMO":
      PROMO -> "P", KVI -> "K", HS -> "H"   (PROMOTIONAL_MAPPING)
      NON PROMO -> ""
      কিছুই না পেলে " " (একটা space — app V3-এর মতো)
    """
    promotional = " "

    m = re.search(
        r"Promotional\s*product.*?(NON\s+PROMO|PROMO|KVI|HS)\b",
        pages_text[0],
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        value = re.sub(r"\s+", " ", m.group(1).strip()).upper()
        if value == "NON PROMO":
            promotional = ""
        else:
            promotional = PROMOTIONAL_MAPPING.get(value, "")

    return promotional


# ================================================================
#  সব একসাথে
# ================================================================
def tc_barcode_columns():
    """["TC_Number_st1".."TC_Number_st7", "Barcode_st1".."Barcode_st7"]"""
    return (
        [f"TC_Number_st{i + 1}" for i in range(V3_MAX_ITEMS)]
        + [f"Barcode_st{i + 1}" for i in range(V3_MAX_ITEMS)]
    )


def extract_inner_outer_fields(pages_text):
    """
    এক PDF থেকে Inner/Outer-এর সব field একটা dict-এ:
      Pictogram, Promotional, Product_name, Inner_kg, Season_st, Inner_qty, Outer_qty,
      TC_Number_st1..st7, Barcode_st1..st7   (কম পেলে বাকিগুলো "")
    """
    tc_numbers = extract_all_tc_numbers(pages_text)
    barcodes = extract_all_barcodes(pages_text)

    fields = {
        "Pictogram": extract_pictogram(pages_text),
        "Promotional": extract_promotional(pages_text),
        "Product_name": extract_product_name(pages_text),
        "Inner_kg": extract_inner_kg(pages_text),
        "Season_st": extract_season_st(pages_text),
        "Inner_qty": extract_inner_qty(pages_text),
        "Outer_qty": extract_outer_qty(pages_text),
    }

    for i in range(V3_MAX_ITEMS):
        fields[f"TC_Number_st{i + 1}"] = tc_numbers[i] if i < len(tc_numbers) else ""

    for i in range(V3_MAX_ITEMS):
        fields[f"Barcode_st{i + 1}"] = barcodes[i] if i < len(barcodes) else ""

    return fields
