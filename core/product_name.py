"""
core/product_name.py
====================
Product name-এর সব function ও logic (SS27 / app 1 থেকে)।

Flow:
  load_product_translations()   Google Sheet (DEPARTMENT, PRODUCT_NAME, EN, ES, AL ... UA)
  render_product_selectors()    Department + Product Type dropdown (PDF থেকে default ঠিক হয়)
  build_material_texts()        AL / MK-র জন্য material নাম ও composition text
  build_product_name()          selected product -> "|EN| ... |AL| ... |UA| ..." string
"""
from urllib.parse import quote

import pandas as pd
import streamlit as st

from core.classification import map_item_class_to_dept_label
from core.config import (
    CACHE_TTL,
    COUNTRY_SUFFIXES,
    LANGUAGE_ORDER,
    MATERIAL_TRANSLATION_LANGS,
    PRODUCT_TRANSLATION_SHEET_ID,
    PRODUCT_TRANSLATION_SHEET_NAME,
)
from core.text_utils import strip_leading_number


# ================================================================
#  PRODUCT TRANSLATION LOADER (Google Sheet)
# ================================================================
@st.cache_data(ttl=CACHE_TTL)
def load_product_translations():
    """Product name translations DataFrame। Fail করলে empty DataFrame।"""
    try:
        sheet_name = quote(PRODUCT_TRANSLATION_SHEET_NAME)
        url = (
            f"https://docs.google.com/spreadsheets/d/{PRODUCT_TRANSLATION_SHEET_ID}"
            f"/gviz/tq?tqx=out:csv&sheet={sheet_name}"
        )
        df = pd.read_csv(url)

        if df.empty:
            st.error("Loaded translations but sheet appears empty")

        return df

    except Exception as e:
        st.error(f"❌ Failed to load translations: {str(e)}")
        return pd.DataFrame()


# ================================================================
#  DEPARTMENT / PRODUCT OPTIONS
# ================================================================
def get_departments(translations_df):
    """Sheet-এর DEPARTMENT column-এর unique নাম।"""
    return translations_df['DEPARTMENT'].dropna().unique().tolist()


def get_products_for_department(translations_df, department):
    """(ওই department-এর rows, PRODUCT_NAME list)।"""
    filtered = translations_df[translations_df['DEPARTMENT'] == department]
    products = filtered['PRODUCT_NAME'].dropna().unique().tolist()
    return filtered, products


def find_default_index(options, target):
    """options-এ target খুঁজে index দেয় (বড়/ছোট হাত ও ফাঁকা জায়গা উপেক্ষা করে)। না পেলে 0।"""
    if target:
        wanted = str(target).strip().lower()
        for i, opt in enumerate(options):
            if str(opt).strip().lower() == wanted:
                return i
    return 0


def render_product_selectors(
    translations_df,
    item_class,
    item_name_en,
    key_prefix="ui_",
    dept_col=None,
    product_col=None,
):
    """
    "Select Department" আর "Select Product Type" dropdown দেখায়।
      - Department default = Item classification থেকে (যেমন Younger Girls -> Girls)
      - Product default    = PDF-এর Item name (শুরুর "4." বাদ দিয়ে)
    dept_col / product_col: st.columns()-এর column দিলে সেখানে বসবে।
    key_prefix: প্রতি mode-এ আলাদা দিন (যেমন "ss27_ui_") — widget key clash এড়াতে।

    Return: (selected_dept, product_type, filtered_df)
    """
    if dept_col is None:
        dept_col = st.container()
    if product_col is None:
        product_col = st.container()

    depts = get_departments(translations_df)
    dept_index = find_default_index(depts, map_item_class_to_dept_label(item_class))

    with dept_col:
        selected_dept = st.selectbox(
            "Select Department",
            options=depts,
            index=dept_index,
            key=f"{key_prefix}dept",
        )

    filtered, products = get_products_for_department(translations_df, selected_dept)
    product_index = find_default_index(products, strip_leading_number(item_name_en or ""))

    with product_col:
        product_type = st.selectbox(
            "Select Product Type",
            options=products,
            index=product_index,
            key=f"{key_prefix}product",
        )

    return selected_dept, product_type, filtered


# ================================================================
#  MATERIAL TEXT FOR AL / MK
# ================================================================
def build_material_texts(valid_rows, material_translations_df):
    """
    valid_rows: [{"mat": "Cotton", "pct": 50}, ...]
    Return: (material_trans_dict, material_compositions)
      material_trans_dict   = {"AL": "Pambuk, Poliester", "MK": ...}   (শুধু নাম)
      material_compositions = {"AL": "50% Pambuk, 50% Poliester", ...} (% সহ)
    """
    material_trans_dict = {}
    material_compositions = {}

    if not valid_rows or material_translations_df.empty:
        return material_trans_dict, material_compositions

    for lang in MATERIAL_TRANSLATION_LANGS:
        names, comp = [], []

        for r in valid_rows:
            t = material_translations_df[
                (material_translations_df['material'] == r['mat']) &
                (material_translations_df['language'] == lang)
            ]
            if t.empty:
                continue

            tr = t['translation'].iloc[0]
            if pd.isna(tr) or not str(tr).strip():
                continue  # ফাঁকা translation বাদ

            names.append(tr)
            comp.append(f"{r['pct']}% {tr}")

        if names:
            material_trans_dict[lang] = ", ".join(names)
        if comp:
            material_compositions[lang] = ", ".join(comp)

    return material_trans_dict, material_compositions


# ================================================================
#  PRODUCT NAME FORMATTER
# ================================================================
def _text_or(value, fallback):
    """ফাঁকা / NaN হলে fallback (product name) দেয়।"""
    if value is None or pd.isna(value) or not str(value).strip():
        return fallback
    return str(value)


def format_product_translations(
    product_name,
    translation_row,
    selected_materials=None,
    material_translations=None,
    material_compositions=None,
):
    """
    Multilingual product description বানায়:
      |EN| ... |AL| ... |BG| ... |UA| ...
    AL ও MK-তে material info (": 100% Pambuk") যোগ হয়; BiH, RS, UA-তে দেশ অনুযায়ী suffix।
    Sheet-এ কোনো ভাষার cell ফাঁকা থাকলে product name বসে (আগে "nan" লেখা হত)।
    """
    formatted = []

    # EN
    en_text = _text_or(translation_row.get('EN'), product_name)
    formatted.append(f"|EN| {en_text}")

    # ES = ES / ES_CA (Catalan থাকলে)
    es_text = _text_or(translation_row.get('ES'), product_name)
    es_ca = translation_row.get('ES_CA')
    if pd.notna(es_ca) and str(es_ca).strip():
        es_text = f"{es_text} / {es_ca}"
    combined_lang = {'ES': es_text}

    for lang in LANGUAGE_ORDER:
        if lang in combined_lang:
            text = combined_lang[lang]
        else:
            text = _text_or(translation_row.get(lang), product_name)

        # Material নাম / composition — শুধু AL + MK
        if selected_materials and material_translations and lang in MATERIAL_TRANSLATION_LANGS:
            comp = (material_compositions or {}).get(lang, "")
            names = material_translations.get(lang, "")

            if comp:
                text = f"{text}: {comp}"
            elif names:
                text = f"{text}: {names}"

        # দেশ অনুযায়ী suffix
        if lang in COUNTRY_SUFFIXES:
            if not text.endswith('.'):
                text += "."
            text += COUNTRY_SUFFIXES[lang]

        formatted.append(f"|{lang}| {text}")

    return " ".join(formatted)


def build_product_name(
    product_type,
    filtered_df,
    selected_materials=None,
    material_trans_dict=None,
    material_compositions=None,
):
    """
    Selected product-এর row খুঁজে পুরো product_name string বানায়।
    row না পেলে "" (app 1-এর মতো)।
    """
    product_row = filtered_df[filtered_df['PRODUCT_NAME'] == product_type]
    if product_row.empty:
        return ""

    return format_product_translations(
        product_type,
        product_row.iloc[0],
        selected_materials,
        material_trans_dict,
        material_compositions,
    )
