"""
core/loaders.py
===============
Google Sheet loader (10 মিনিট cache)।
Price ladder-এর loader -> core/price.py, Product translation-এর loader -> core/product_name.py
URL / gid / fallback data সব core/config.py থেকে আসে।
"""
import pandas as pd
import streamlit as st

from core.config import (
    CACHE_TTL,
    MATERIAL_TRANSLATION_SHEET_URL,
    MATERIAL_TRANSLATION_LANGS,
    MATERIAL_TRANSLATION_FALLBACK,
    CARE_SHEET_BASE_URL,
    CARE_SHEET_GIDS,
    COMPONENT_TRANSLATION_FALLBACK,
)


# ================================================================
#  MATERIAL TRANSLATIONS (SS27 + Care)
# ================================================================
@st.cache_data(ttl=CACHE_TTL)
def load_material_translations():
    """Material translations (AL, MK) → columns: material, language, translation."""
    try:
        df = pd.read_csv(MATERIAL_TRANSLATION_SHEET_URL)
        if df.empty:
            raise ValueError("Empty sheet")

        rows = []
        for _, row in df.iterrows():
            name = None
            if 'Name' in row and pd.notna(row['Name']):
                name = row['Name']
            else:
                try:
                    name = row.iloc[0]
                except Exception:
                    name = None

            if not name or pd.isna(name):
                continue

            for lang in MATERIAL_TRANSLATION_LANGS:
                tr = row.get(lang, "")
                tr = "" if pd.isna(tr) else tr
                rows.append({'material': name, 'language': lang, 'translation': tr})

        if not rows:
            raise ValueError("No material rows produced")

        return pd.DataFrame(rows)

    except Exception as e:
        st.warning(f"Could not load material translations ({e}). Using fallback.")
        return pd.DataFrame(MATERIAL_TRANSLATION_FALLBACK)


# ================================================================
#  CARE LABEL & COMPOSITION SHEETS (Care Label)
# ================================================================
@st.cache_data(ttl=CACHE_TTL)
def load_care_composition_data():
    """
    4টা sheet → dict:
      comp_instructions / materials / care_instructions / component_names
    কোনটা load না হলে সেটা empty DataFrame।
    """
    result = {}
    for key, (gid, _name) in CARE_SHEET_GIDS.items():
        url = f"{CARE_SHEET_BASE_URL}?gid={gid}&single=true&output=csv"
        try:
            df = pd.read_csv(url)
            result[key] = df if not df.empty else pd.DataFrame()
        except Exception:
            result[key] = pd.DataFrame()
    return result


@st.cache_data(ttl=CACHE_TTL)
def load_component_translations():
    """Component name translations (EN, AL, BG ...). Sheet না পেলে fallback।"""
    care_data = load_care_composition_data()

    if not care_data["component_names"].empty:
        return care_data["component_names"]

    return pd.DataFrame(COMPONENT_TRANSLATION_FALLBACK)
