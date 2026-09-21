"""
modules/basic_data.py
=====================
Basic Data mode — PDF থেকে শুধু ৬টা field:
  Order_ID, Style, Colour, Supplier_product_code, Item_classification, Supplier_name

Logic app 1 (SS27) থেকে নেওয়া:
  - Order_ID / Style / Supplier / Item_classification -> page 1
  - Style  = page 1-এর প্রথম 6-digit সংখ্যা
  - Colour = auto detect, না পেলে manual input; Title Case (WHITE -> White)
  - একাধিক PDF দিলে বাকি PDF-এর Order ID "+" দিয়ে জোড়া লাগে
"""
import pandas as pd
import streamlit as st

from core.config import BASIC_DATA_COLUMNS
from core.export import build_csv_bytes
from core.pdf_utils import (
    read_pdf_pages,
    extract_header_fields,
    extract_colour_from_pdf_pages,
    split_uploaded_pdfs,
    apply_extra_order_ids,
)

# session_state key prefix — reset-এ "basic_ui_" দিয়ে শুরু হওয়া সব মুছে যায়
_UI = "basic_ui_"
_UPLOADER_COUNTER = "basic_uploader_n"


def extract_basic_data(pages_text):
    """pages_text → (৬-field dict, season)।"""
    h = extract_header_fields(pages_text)
    colour = extract_colour_from_pdf_pages(pages_text, manual_key=f"{_UI}manual_colour")

    row = {
        "Order_ID": h["order_id"],
        "Style": h["style_code"],
        "Colour": colour.title(),
        "Supplier_product_code": h["supplier_code"],
        "Item_classification": h["item_class"],
        "Supplier_name": h["supplier_name"],
    }
    return row, h["season"]


def process_pdf(uploaded_pdf, extra_order_ids=""):
    """PDF → table → edit → CSV download."""
    try:
        pages_text = read_pdf_pages(uploaded_pdf)
        if not pages_text:
            return

        row, season = extract_basic_data(pages_text)
        df = apply_extra_order_ids(pd.DataFrame([row]), extra_order_ids)

        st.success("✅ Done!")
        st.subheader("Edit Before Download")
        edited_df = st.data_editor(df[BASIC_DATA_COLUMNS], key=f"{_UI}editor")

        first = df.iloc[0]
        filename = (
            f"PEPCO_{season.upper()}_Basic "
            f"{first['Supplier_product_code']}_00_{first['Style']}.csv"
        )

        st.download_button(
            "📥 Download CSV",
            build_csv_bytes(BASIC_DATA_COLUMNS, edited_df),
            file_name=filename,
            mime="text/csv",
        )
    except Exception as e:
        st.error(f"PDF error: {str(e)}")


def render():
    """app.py এই function-টা call করে।"""
    st.subheader("📋 PEPCO Basic Data")

    if _UPLOADER_COUNTER not in st.session_state:
        st.session_state[_UPLOADER_COUNTER] = 0

    def _reset_all():
        for k in list(st.session_state.keys()):
            if k.startswith(_UI):
                st.session_state.pop(k, None)
        st.session_state[_UPLOADER_COUNTER] += 1

    cols = st.columns([1, 6])
    with cols[0]:
        st.button("🆕 Upload New File", on_click=_reset_all, key=f"{_UI}reset_btn")

    uploaded_pdfs = st.file_uploader(
        "Upload PEPCO Data file",
        type=["pdf"],
        key=f"basic_uploader_{st.session_state[_UPLOADER_COUNTER]}",
        accept_multiple_files=True,
    )

    if uploaded_pdfs:
        primary_pdf, extra_ids = split_uploaded_pdfs(uploaded_pdfs)
        process_pdf(primary_pdf, extra_order_ids=extra_ids)
