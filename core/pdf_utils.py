"""
core/pdf_utils.py
=================
তিনটা app-এ যে PDF-related code হুবহু (বা প্রায় হুবহু) এক ছিল সব এখানে।

  read_pdf_pages            -> PDF → page-wise text
  extract_header_fields     -> Order ID, Style, Supplier, Season, Item name ...
  extract_skus_and_barcodes -> SS27 + Care
  extract_skus              -> Label V3 (barcode লাগে না)
  extract_colour_from_pdf_pages
  extract_order_id_only / split_uploaded_pdfs / apply_extra_order_ids
"""
import re

import fitz  # PyMuPDF
import streamlit as st


# ================================================================
#  SMALL HELPERS
# ================================================================
def dedupe(seq):
    """Order ঠিক রেখে duplicate বাদ দেয়।"""
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _seek(file, pos=0):
    try:
        file.seek(pos)
    except Exception:
        pass


# ================================================================
#  READ PDF
# ================================================================
def read_pdf_pages(file):
    """
    Uploaded PDF → page-wise text-এর list। সমস্যা হলে error দেখিয়ে None।
    (পড়ার আগে file pointer 0-তে নেওয়া হয়, তাই rerun-এ empty আসবে না)
    """
    try:
        _seek(file, 0)
        raw = file.read()
        if not raw:
            st.error("Empty PDF uploaded.")
            return None

        with fitz.open(stream=raw, filetype="pdf") as doc:
            if len(doc) < 1:
                st.error("PDF must have at least 1 page.")
                return None
            return [page.get_text() for page in doc]

    except Exception as e:
        st.error(f"PDF error: {str(e)}")
        return None


# ================================================================
#  HEADER FIELDS (page 1 + full text)
# ================================================================
def extract_header_fields(pages_text):
    """
    তিনটা app-এ যেসব field একইভাবে বের হত:
      item_name_en, order_id, style_code (page1-এর প্রথম 6-digit),
      item_class, supplier_code, supplier_name, season (SS27), season_yy (27)
    না পেলে "UNKNOWN" (item_name_en না পেলে "")।
    """
    page1 = pages_text[0]
    full_text = "\n".join(pages_text)

    # Item name EN
    m_item = re.search(r"Item\s*name\s*English\s*[:\.]{1,}\s*(.+)", full_text, re.IGNORECASE)
    if not m_item:
        m_item = re.search(r"Item\s*name\s*[:\.]{1,}\s*(.+?)\n", full_text, re.IGNORECASE)
    item_name_en = m_item.group(1).strip() if m_item else ""

    def _first(pattern):
        m = re.search(pattern, page1)
        return m.group(1).strip() if m else "UNKNOWN"

    style = re.search(r"\b\d{6}\b", page1)
    season = re.search(r"Season\s*\.{2,}\s*(\w+)?\s*(\d{2})", page1)

    return {
        "item_name_en": item_name_en,
        "order_id": _first(r"Order\s*-\s*ID\s*\.{2,}\s*(.+)"),
        "style_code": style.group() if style else "UNKNOWN",
        "item_class": _first(r"Item classification\s*\.{2,}\s*(.+)"),
        "supplier_code": _first(r"Supplier product code\s*\.{2,}\s*(.+)"),
        "supplier_name": _first(r"Supplier name\s*\.{2,}\s*(.+)"),
        "season": f"{season.group(1) or ''}{season.group(2)}" if season else "UNKNOWN",
        "season_yy": season.group(2) if season else "",
    }


# ================================================================
#  SKU + BARCODE
# ================================================================
def extract_skus_and_barcodes(pages_text):
    """
    8-digit SKU আর 13-digit barcode বের করে (SS27 + Care)।
    "barcode: xxxxxxxxxxxxx" লেখা barcode গুলো বাদ যায়।
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


# ================================================================
#  COLOUR
# ================================================================
def detect_colour(pages_text):
    """
    PEPCO Colour detection (5-page / 6-page PDF, broken layout, pantone ছাড়া)।
    কিছু না পেলে None (UI ছাড়া pure function)।
    """
    # 1) Standard Colour table
    for txt in pages_text:
        m = re.search(
            r"Colour.*?\n.*?\n\s*([A-Za-z ]+)\s+[0-9]{2}-[0-9]{4}",
            txt, re.IGNORECASE | re.DOTALL
        )
        if m:
            return m.group(1).strip().upper()

    # 2) Purchase price block
    for txt in pages_text:
        m2 = re.search(
            r"Purchase price.*?\n\s*([A-Za-z ]+)\s+[0-9]{2}-[0-9]{4}",
            txt, re.IGNORECASE | re.DOTALL
        )
        if m2:
            return m2.group(1).strip().upper()

    # 3) Generic fallback — "colour" শব্দ আছে এমন page-এর লাইন
    for txt in pages_text:
        if "colour" in txt.lower():
            for line in txt.splitlines():
                if re.search(r"[A-Za-z ]+\s+[0-9]{2}-[0-9]{4}", line):
                    name = line.split()[0:-1]
                    if name:
                        return " ".join(name).upper()

    return None


def extract_colour_from_pdf_pages(pages_text, manual_key="manual_colour_fix"):
    """
    Colour বের করে; না পেলে user-কে manual input দেখায়।
    manual_key: প্রতি mode-এ আলাদা দিন (যেমন "ss27_manual_colour") — widget key clash এড়াতে।
    """
    colour = detect_colour(pages_text)
    if colour:
        return colour

    st.warning("⚠️ Colour not found in PDF. Enter colour manually:")
    manual = st.text_input("Colour (e.g. WHITE):", key=manual_key)
    return manual.strip().upper() if manual else "UNKNOWN"


# ================================================================
#  MULTIPLE PDF UPLOAD → EXTRA ORDER IDS
# ================================================================
def extract_order_id_only(file):
    """একটা PDF থেকে শুধু Order ID (file pointer আগের জায়গায় ফেরত রাখে)।"""
    pos = None
    try:
        pos = file.tell()
    except Exception:
        pass

    _seek(file, 0)

    try:
        with fitz.open(stream=file.read(), filetype="pdf") as doc:
            page1_text = doc[0].get_text() if len(doc) > 0 else ""
    except Exception:
        _seek(file, 0 if pos is None else pos)
        return None

    _seek(file, 0 if pos is None else pos)

    m = re.search(r"Order\s*-\s*ID\s*\.{2,}\s*([A-Z0-9_+-]+)", page1_text, re.IGNORECASE)
    return m.group(1).strip() if m else None


def split_uploaded_pdfs(uploaded_pdfs):
    """
    accept_multiple_files=True এর result থেকে:
      primary_pdf  = প্রথম PDF
      extra_ids    = বাকি PDF-এর Order ID গুলো "+" দিয়ে জোড়া ("" হতে পারে)
    """
    if not isinstance(uploaded_pdfs, list):
        uploaded_pdfs = [uploaded_pdfs]

    primary_pdf = uploaded_pdfs[0]
    other_ids = []

    for f in uploaded_pdfs[1:]:
        _seek(f, 0)
        oid = extract_order_id_only(f)
        if oid:
            other_ids.append(oid)
        _seek(f, 0)

    return primary_pdf, "+".join(other_ids)


def apply_extra_order_ids(df, extra_order_ids):
    """DataFrame-এর Order_ID-তে বাকি PDF-এর ID গুলো "+" দিয়ে জুড়ে দেয়।"""
    if extra_order_ids:
        try:
            df["Order_ID"] = df["Order_ID"].astype(str) + "+" + extra_order_ids
        except Exception:
            pass
    return df
