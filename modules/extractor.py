"""
modules/extractor.py
====================
PEPCO Data Extractor — একটাই mode, একটাই CSV।

PDF থেকে (Order, Style, Colour, Collection, Batch, SKU, Barcode, Sizes, PL price
          + page 4+ এর Inner/Outer data)
  -> Department, Product Type, Washing Code, PLN price বাছাই
  -> একটা table (প্রতি SKU-তে ১ row) -> Edit -> একটাই CSV

Column: core/config.py-র UNIFIED_COLUMNS (আগের তিন app-এর সব column একসাথে)।
Inner/Outer field (Pictogram, TC, Barcode_st ...) একই PDF-এর সব row-তে একই থাকে।

এখনো নেই: Size (Care, cm), Composition_Care, Material %, Cotton flag।
"""
from datetime import datetime

import pandas as pd
import streamlit as st

from core.batch import build_style_merch_season, extract_batch, format_batch_label
from core.classification import get_dept_value
from core.collection import extract_collection, modify_collection
from core.config import (
    CSV_FILENAME_TAG,
    DEFAULT_WASHING_CODE,
    ITEM_NAME_PREFIXES_SS27,
    UNIFIED_COLUMNS,
    WASHING_CODES,
)
from core.export import build_csv_bytes
from core.inner_outer import extract_inner_outer_fields
from core.pdf_utils import (
    apply_extra_order_ids,
    extract_colour_from_pdf_pages,
    extract_header_fields,
    read_pdf_pages,
    split_uploaded_pdfs,
)
from core.price import add_price_columns, extract_pl_sales_price_from_pdf, parse_pln_price
from core.product_name import (
    build_product_name,
    load_product_translations,
    render_product_selectors,
)
from core.size import extract_sizes_from_pdf, pair_sizes, split_sizes
from core.sku_barcode import build_colour_sku, extract_skus_and_barcodes, join_skus_for_filename
from core.text_utils import clean_item_name_english

# session_state key prefix — reset-এ "ext_ui_" দিয়ে শুরু হওয়া সব মুছে যায়
_UI = "ext_ui_"
_UPLOADER_COUNTER = "ext_uploader_n"


# ================================================================
#  PDF -> ROWS
# ================================================================
def extract_rows(pages_text):
    """
    PDF-এর সব field বের করে প্রতি SKU/barcode জোড়ায় ১টা row বানায়।
    Return: (rows, detected_pl, skus)। SKU/Barcode না পেলে None।
    """
    h = extract_header_fields(pages_text)
    detected_pl = extract_pl_sales_price_from_pdf(pages_text)
    sizes = split_sizes(extract_sizes_from_pdf(pages_text))

    # (widget-এর ক্রম: আগে Collection, তারপর Colour — app 1-এর মতো)
    collection = extract_collection(pages_text, h["item_class"], manual_key=f"{_UI}manual_collection")
    batch = extract_batch(pages_text)
    colour = extract_colour_from_pdf_pages(pages_text, manual_key=f"{_UI}manual_colour")

    skus, barcodes = extract_skus_and_barcodes(pages_text)
    if not skus:
        return None
    sizes = pair_sizes(sizes, len(skus))

    today = datetime.today().strftime("%d-%m-%Y")
    style_line = build_style_merch_season(h["style_code"], h["merch_code"], h["season_yy"])
    batch_label = format_batch_label(batch)
    inner_outer = extract_inner_outer_fields(pages_text)   # সব row-তে একই

    rows = []
    for sku, barcode, size in zip(skus, barcodes, sizes):
        rows.append({
            "Order_ID": h["order_id"],
            "Style": h["style_code"],
            "Colour": colour.title(),
            "Supplier_product_code": h["supplier_code"],
            "Item_classification": h["item_class"],
            "Supplier_name": h["supplier_name"],
            "today_date": today,
            "Collection": collection,
            "Colour_SKU": build_colour_sku(colour, sku),
            "Style_Merch_Season": style_line,
            "Batch": batch_label,
            "barcode": barcode,
            "Item_name_EN": h["item_name_en"],
            "Season": h["season"],
            "Sizes": size,
            "SKU_Name": sku,
            **inner_outer,
        })

    return rows, detected_pl, skus


# ================================================================
#  MATERIAL (পরে material.py আসলে এখানে বসবে)
# ================================================================
def _material_section():
    """
    Return: (selected_materials, material_trans_dict, material_compositions, cotton_value)
    এখন কোনো material নেই।
    """
    st.caption(
        "ℹ️ Material Composition আর Cotton flag এখনো যোগ হয়নি — "
        "product_name-এ AL/MK-তে material text আসবে না।"
    )
    return [], {}, {}, ""


# ================================================================
#  MAIN PIPELINE
# ================================================================
def process_pdf(uploaded_pdf, extra_order_ids=""):
    """PDF -> table -> (Department, Product, Washing, PLN) -> একটাই CSV।"""
    try:
        translations_df = load_product_translations()
        if translations_df.empty:
            return  # loader নিজেই error দেখিয়েছে

        pages_text = read_pdf_pages(uploaded_pdf)
        if not pages_text:
            return

        extracted = extract_rows(pages_text)
        if not extracted:
            return
        rows, detected_pl, skus = extracted

        df = apply_extra_order_ids(pd.DataFrame(rows), extra_order_ids)
        first = rows[0]

        # ---------- Department / Product / Washing / PLN ----------
        c1, c2, c3, c4 = st.columns(4)

        _dept, product_type, filtered = render_product_selectors(
            translations_df,
            first["Item_classification"],
            first["Item_name_EN"],
            key_prefix=_UI,
            dept_col=c1,
            product_col=c2,
        )

        washing_options = list(WASHING_CODES.keys())
        wash_index = washing_options.index(DEFAULT_WASHING_CODE) if DEFAULT_WASHING_CODE in washing_options else 0
        with c3:
            washing_key = st.selectbox(
                "Select Washing Code", options=washing_options, index=wash_index, key=f"{_UI}wash"
            )

        with c4:
            pln_raw = st.text_input(
                "Enter PLN Price",
                value=str(detected_pl) if detected_pl else "",
                key=f"{_UI}pln_price",
            )
        pln_price = parse_pln_price(pln_raw)

        # ---------- Material (পরে) ----------
        selected_materials, mat_names, mat_comp, cotton_value = _material_section()

        # ---------- Table enrich ----------
        df["Dept"] = df["Item_classification"].apply(get_dept_value)
        if cotton_value == "Z":
            df["Cotton"] = cotton_value

        df["Collection"] = df.apply(
            lambda r: modify_collection(r["Collection"], r["Item_classification"]), axis=1
        )
        df["product_name"] = build_product_name(
            product_type, filtered, selected_materials, mat_names, mat_comp
        )
        df["washing_code"] = WASHING_CODES[washing_key]
        df["Item_name_English"] = df["Item_name_EN"].apply(
            lambda n: clean_item_name_english(n, ITEM_NAME_PREFIXES_SS27)
        )

        # ---------- দাম ----------
        priced = add_price_columns(df, pln_price)
        if priced is not None:
            df = priced
        elif pln_price is None:
            st.warning("⚠️ PLN price দেওয়া হয়নি — দামের column গুলো ফাঁকা থাকবে।")
        # (ladder-এ না মিললে add_price_columns নিজেই warning দেখিয়েছে; দামের column ফাঁকা থাকবে)

        # ---------- Final table + CSV ----------
        final_cols = list(UNIFIED_COLUMNS)
        if "Cotton" in df.columns and "Cotton" not in final_cols:
            final_cols.append("Cotton")
        for col in final_cols:
            if col not in df.columns:
                df[col] = ""

        st.success("✅ Done!")
        st.subheader("Edit Before Download")
        edited_df = st.data_editor(df[final_cols])

        top = df.iloc[0]
        filename = (
            f"PEPCO_{str(top['Season']).upper()}_{join_skus_for_filename(skus)}_"
            f"{CSV_FILENAME_TAG} {top['Supplier_product_code']}_00_{top['Style']}.csv"
        )

        st.download_button(
            "📥 Download CSV",
            build_csv_bytes(final_cols, edited_df),
            file_name=filename,
            mime="text/csv",
        )

    except Exception as e:
        st.error(f"PDF error: {str(e)}")


# ================================================================
#  UI ENTRY
# ================================================================
def render():
    """app.py এই function-টা call করে।"""
    st.subheader("📄 PEPCO Data Processing")

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
        key=f"ext_uploader_{st.session_state[_UPLOADER_COUNTER]}",
        accept_multiple_files=True,
    )

    if uploaded_pdfs:
        primary_pdf, extra_ids = split_uploaded_pdfs(uploaded_pdfs)
        process_pdf(primary_pdf, extra_order_ids=extra_ids)
