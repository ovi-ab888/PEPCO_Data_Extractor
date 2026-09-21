# ================================================================
# PART 1 — PAGE CONFIG + IMPORTS
# ================================================================

# ---------- PAGE CONFIG (must be at top) ----------
import streamlit as st
st.set_page_config(
    page_title="PEPCO SS27",
    page_icon="🧾",
    layout="wide"
)

# ---------- Imports ----------
import pandas as pd
import re
from io import StringIO
import csv as pycsv
import requests

# ---------- Local modules (same folder) ----------
from pdf_extractor import extract_data_from_pdf, extract_order_id_only
from auto_fields import get_dept_value, clean_item_name_english
from constants import WASHING_CODES, COLLECTION_MAPPING


# ================================================================
# PART 2 — DATA LOADERS + HELPER FUNCTIONS
# ================================================================

# ================================================================
#  PRICE DATA LOADER (Google Sheet)
# ================================================================
@st.cache_data(ttl=600)
def load_price_data():
    """Load currency price ladder from Google Sheet."""
    try:
        url = (
            "https://docs.google.com/spreadsheets/d/e/"
            "2PACX-1vRdAQmBHwDEWCgmLdEdJc0HsFYpPSyERPHLwmr2tnTYU1BDWdBD6I0ZYfEDzataX0wTNhfLfnm-Te6w/"
            "pub?gid=583402611&single=true&output=csv"
        )
        df = pd.read_csv(url)

        if df.empty:
            st.error("Price data sheet is empty")
            return None

        # Convert to dictionary {currency: [values]}
        price_data = {}
        for currency in df.columns:
            price_data[currency] = df[currency].dropna().tolist()

        return price_data

    except Exception as e:
        st.error(f"Failed to load price data: {str(e)}")
        return None


# ================================================================
#  PRODUCT TRANSLATION LOADER
# ================================================================
@st.cache_data(ttl=600)
def load_product_translations():
    """Load product name translations from Google Sheet."""
    try:
        sheet_id = "1ue68TSJQQedKa7sVBB4syOc0OXJNaLS7p9vSnV52mKA"
        sheet_name = "SS26 Product_Name"
        encoded = requests.utils.quote(sheet_name)

        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={encoded}"
        df = pd.read_csv(url)

        if df.empty:
            st.error("Loaded translations but sheet appears empty")

        return df

    except Exception as e:
        st.error(f"❌ Failed to load translations: {str(e)}")
        return pd.DataFrame()


# ================================================================
#  MATERIAL TRANSLATION LOADER
# ================================================================
@st.cache_data(ttl=600)
def load_material_translations():
    """Load material translations (AL, MK) with fallback."""
    try:
        url = (
            "https://docs.google.com/spreadsheets/d/e/"
            "2PACX-1vRdAQmBHwDEWCgmLdEdJc0HsFYpPSyERPHLwmr2tnTYU1BDWdBD6I0ZYfEDzataX0wTNhfLfnm-Te6w/"
            "pub?gid=1096440227&single=true&output=csv"
        )
        df = pd.read_csv(url)

        # Empty → go fallback
        if df.empty:
            st.warning("Material translations sheet empty — using fallback.")
            raise ValueError("Empty sheet")

        material_translations = []

        for _, row in df.iterrows():
            # Material name
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

            # Add AL & MK groups
            for lang in ['AL', 'MK']:
                tr = row.get(lang, "")
                tr = "" if pd.isna(tr) else tr

                material_translations.append({
                    'material': name,
                    'language': lang,
                    'translation': tr
                })

        if not material_translations:
            raise ValueError("No material rows produced")

        return pd.DataFrame(material_translations)

    except Exception as e:
        # Fallback
        st.warning(f"Could not load material translations ({e}). Using fallback.")
        fallback = [
            {'material': 'Cotton', 'language': 'AL', 'translation': 'Cotton'},
            {'material': 'Cotton', 'language': 'MK', 'translation': 'Cotton'}
        ]
        return pd.DataFrame(fallback)


# ================================================================
#  HELPER FUNCTIONS
# ================================================================

# ---------- Format numbers (PLN, EUR, RON, etc) ----------
def format_number(value, currency):
    """Format numeric pricing based on currency."""
    try:
        if isinstance(value, str):
            value = float(value.replace(',', '.'))

        if currency in ['EUR', 'BGN', 'BAM', 'RON', 'PLN']:
            formatted = f"{float(value):,.2f}".replace(".", ",")

            if ',' in formatted:
                parts = formatted.split(',')
                parts[0] = parts[0].replace('.', '')  # remove thousand separator
                formatted = ','.join(parts)

            return formatted

        return str(int(float(value)))

    except (ValueError, TypeError):
        return str(value)


# ---------- Match PLN to price ladder ----------
def find_closest_price(pln_value):
    """Returns matching row of other currencies for the PLN price."""
    try:
        price_data = load_price_data()

        if not price_data or 'PLN' not in price_data:
            st.error("❌ Price data not available")
            return None

        pln_value = float(pln_value)
        ladder = price_data['PLN']

        if pln_value not in ladder:
            st.error(f"❌ PLN {pln_value} not found in price sheet.")
            return None

        idx = ladder.index(pln_value)

        return {
            currency: format_number(values[idx], currency)
            for currency, values in price_data.items()
            if currency != 'PLN'
        }

    except Exception as e:
        st.error(f"Invalid price value: {str(e)}")
        return None


# ---------- Classification → mapping ----------
def get_classification_type(item_class):
    """Determine class type key used in COLLECTION_MAPPING."""
    if not item_class:
        return None

    ic = item_class.lower()

    if 'younger girls outerwear' in ic:
        return 'yg'
    if 'older girls outerwear' in ic:
        return 'og'
    if 'younger boys outerwear' in ic:
        return 'yb'
    if 'older boys outerwear' in ic:
        return 'ob'
    if 'baby girls outerwear' in ic:
        return 'a'
    if 'baby boys outerwear' in ic:
        return 'b'
    if 'baby girls essentials' in ic:
        return 'd_girls'
    if 'baby boys essentials' in ic:
        return 'd'
    if 'ladies outerwear' in ic:
        return 'l'
    if 'mens outerwear' in ic:
        return 'm'

    return None


# ---------- Map Item_classification → Dept label (UI dropdown default) ----------
def map_item_class_to_dept_label(item_class):
    """Map item_class text to UI Department names."""
    if not item_class:
        return None

    ic = item_class.lower()

    if 'baby boys outerwear' in ic or 'baby boys essentials' in ic:
        return "Baby Boy"
    if 'baby girls outerwear' in ic or 'baby girls essentials' in ic:
        return "Baby Girl"
    if 'younger boys outerwear' in ic or 'older boys outerwear' in ic:
        return "Boys"
    if 'younger girls outerwear' in ic or 'older girls outerwear' in ic:
        return "Girls"
    if 'ladies outerwear' in ic:
        return "Women"
    if 'mens outerwear' in ic:
        return "Mens"

    return None


# ---------- Modify collection name (add B/G) ----------
def modify_collection(collection, item_class):
    """Append B/G based on gender groups."""
    if not item_class:
        return collection

    ic = item_class.lower()

    if any(x in ic for x in ['younger boys', 'older boys']):
        return f"{collection} B"

    if any(x in ic for x in ['younger girls', 'older girls']):
        return f"{collection} G"

    return collection


# ================================================================
# PART 3 — TRANSLATION FORMATTER
# ================================================================

# ================================================================
#  TRANSLATION FORMATTER (AL, ES, MK, etc)
# ================================================================
def format_product_translations(
    product_name,
    translation_row,
    selected_materials=None,
    material_translations=None,
    material_compositions=None
):
    """Builds multilingual product description with material info."""
    formatted = []

    # Country suffix rules
    country_suffixes = {
        'BiH': " Sastav materijala na ušivenoj etiketi.",
        'RS': " Sastav materijala nalazi se na ušivenoj etiketi.",
        'UA': " Імпортер приймає претензії. Термін придатності – необмежений, якщо продукт використовується за призначенням (якщо на упаковці або продукті не вказано термін придатності). Умови зберігання – Зберігати в сухому місці при кімнатній температурі.",
    }

    # EN fallback
    en_text = translation_row.get('EN', product_name)
    formatted.append(f"|EN| {en_text}")

    # ES / ES_CA combined
    combined_lang = {
        'ES': (
            f"{translation_row['ES']} / {translation_row['ES_CA']}"
            if pd.notna(translation_row.get('ES_CA'))
            else translation_row.get('ES')
        )
    }

    # Language order defined
    language_order = [
        'AL', 'BG', 'BiH', 'CZ', 'DE', 'EE',
        'ES', 'GR', 'HR', 'HU', 'IT', 'LT',
        'LV', 'MK', 'PL', 'PT', 'RO', 'RS',
        'SI', 'SK', 'UA'
    ]

    # Build translations
    for lang in language_order:
        if lang in combined_lang and combined_lang[lang] is not None:
            text = combined_lang[lang]
        else:
            text = translation_row.get(lang, product_name)

        # Material names or composition for AL + MK only
        if selected_materials and material_translations and lang in ['AL', 'MK']:
            comp = (material_compositions or {}).get(lang, "")
            names = material_translations.get(lang, "")

            if comp:
                text = f"{text}: {comp}"
            elif names:
                text = f"{text}: {names}"

        # Country suffix
        if lang in country_suffixes:
            if not text.endswith('.'):
                text += "."
            text += country_suffixes[lang]

        formatted.append(f"|{lang}| {text}")

    return " ".join(formatted)


# ================================================================
# PART 4 — MAIN PROCESSOR + UI SECTION + APP ENTRY
# ================================================================

# ================================================================
#  MAIN WORKFLOW: PDF → DataFrame → UI → CSV
# ================================================================
def process_pepco_pdf(uploaded_pdf, extra_order_ids: str | None = None):
    """Main pipeline: parse PDF, build DF, apply UI choices, export CSV."""
    # ----- Load reference data -----
    translations_df = load_product_translations()
    material_translations_df = load_material_translations()

    if not (uploaded_pdf and not translations_df.empty):
        return

    # ----- Parse PDF to structured data -----
    result_data, detected_pl = extract_data_from_pdf(uploaded_pdf)
    if not result_data:
        return

    df = pd.DataFrame(result_data)

    # ----- Collection mapping (age extractor-er bhitore chilo) -----
    def _map_collection(row):
        class_type = get_classification_type(row["Item_classification"])
        collection = str(row["Collection"])
        if class_type and class_type in COLLECTION_MAPPING:
            for orig, new in COLLECTION_MAPPING[class_type].items():
                if orig.upper() in collection.upper():
                    return new
        return collection

    df["Collection"] = df.apply(_map_collection, axis=1)

    # ----- Base values from first row -----
    first_row = result_data[0] if len(result_data) > 0 else {}
    pdf_item_class = first_row.get("Item_classification", "")
    pdf_item_name_en = (first_row.get("Item_name_EN") or "").strip()
    pdf_item_name_en = re.sub(r'^\d+\.\s*', '', pdf_item_name_en).strip()

    # ----- Merge extra Order IDs from other PDFs -----
    if extra_order_ids:
        try:
            df['Order_ID'] = df['Order_ID'].astype(str) + "+" + extra_order_ids
        except Exception:
            pass

    # ============================================================
    #  UI Controls (Department, Product, Washing, PLN)
    # ============================================================
    c1, c2, c3, c4 = st.columns(4)

    # -- Department select (default from item_class) --
    depts = translations_df['DEPARTMENT'].dropna().unique().tolist()
    default_dept_label = map_item_class_to_dept_label(pdf_item_class)
    default_dept_index = 0

    if default_dept_label:
        for i, d in enumerate(depts):
            if str(d).strip().lower() == str(default_dept_label).strip().lower():
                default_dept_index = i
                break

    with c1:
        selected_dept = st.selectbox(
            "Select Department",
            options=depts,
            index=default_dept_index,
            key="ui_dept"
        )

    # -- Product list filtered by Department --
    filtered = translations_df[translations_df['DEPARTMENT'] == selected_dept]
    products = filtered['PRODUCT_NAME'].dropna().unique().tolist()

    default_product_index = 0
    if pdf_item_name_en:
        for i, p in enumerate(products):
            if str(p).strip().lower() == pdf_item_name_en.strip().lower():
                default_product_index = i
                break

    with c2:
        product_type = st.selectbox(
            "Select Product Type",
            options=products,
            index=default_product_index,
            key="ui_product"
        )

    # -- Washing code --
    washing_options = list(WASHING_CODES.keys())
    washing_default_index = washing_options.index('9') if '9' in washing_options else 0

    with c3:
        washing_code_key = st.selectbox(
            "Select Washing Code",
            options=washing_options,
            index=washing_default_index,
            key="ui_wash"
        )

    # -- PLN price manual input --
    with c4:
        default_pln = str(detected_pl) if detected_pl else ""
        pln_price_raw = st.text_input(
            "Enter PLN Price",
            value=default_pln,
            key="ui_pln_price"
        )

    # ============================================================
    #  Parse PLN price
    # ============================================================
    pln_price = None
    if pln_price_raw.strip():
        try:
            pln_price = float(pln_price_raw.replace(",", "."))
            if pln_price < 0:
                st.error("❌ Price can't be negative.")
                pln_price = None
        except ValueError:
            st.error("❌ Please enter a valid number like 12.50 or 12,50")
            pln_price = None

    # ============================================================
    #  MATERIAL COMPOSITION UI
    # ============================================================
    st.markdown("### Material Composition (%)")

    # Session init
    if "mat_rows" not in st.session_state:
        st.session_state.mat_rows = 1
    if "mat_data" not in st.session_state:
        st.session_state.mat_data = [{"mat": "Cotton", "pct": 100}]

    materials_list = (
        material_translations_df['material'].dropna().unique().tolist()
        if not material_translations_df.empty else []
    )
    if "Cotton" not in materials_list:
        materials_list = ["Cotton"] + materials_list

    def _ensure_row(i):
        while i >= len(st.session_state.mat_data):
            st.session_state.mat_data.append({"mat": None, "pct": 0})

    # ------ Per-row UI ------
    for i in range(st.session_state.mat_rows):
        _ensure_row(i)

        prev_total = sum(r["pct"] for r in st.session_state.mat_data[:i] if r["pct"])
        remain = max(0, 100 - prev_total)

        cA, cB = st.columns([3, 1.3])

        # Material select
        with cA:
            cur_mat = st.session_state.mat_data[i]["mat"]
            options = ["—"] + materials_list
            idx = options.index(cur_mat) if (cur_mat in options) else 0

            st.session_state.mat_data[i]["mat"] = st.selectbox(
                "Select Material(s)" if i == 0 else f"Select Material(s) #{i+1}",
                options,
                index=idx,
                key=f"mat_sel_{i}"
            )

        # Percentage input
        with cB:
            cur_pct = st.session_state.mat_data[i]["pct"]
            default_pct = (
                100 if (i == 0 and not cur_pct and st.session_state.mat_data[i]["mat"] == "Cotton")
                else min(cur_pct, remain)
            )

            if i == 0 and st.session_state.mat_data[i]["mat"] == "Cotton" and cur_pct in (None, 0):
                default_pct = 100
                st.session_state.mat_data[i]["pct"] = 100

            st.session_state.mat_data[i]["pct"] = st.number_input(
                "Composition (%)" if i == 0 else f"Composition (%) #{i+1}",
                min_value=0,
                max_value=remain,
                step=1,
                value=default_pct,
                key=f"mat_pct_{i}"
            )

    # Valid rows
    valid_rows = [
        r for r in st.session_state.mat_data[:st.session_state.mat_rows]
        if r["mat"] not in (None, "—") and r["pct"] > 0
    ]
    running_total = sum(r["pct"] for r in valid_rows)

    # Auto-add next material row
    if running_total < 100 and st.session_state.mat_rows < 5:
        last = st.session_state.mat_data[st.session_state.mat_rows - 1]
        if last["mat"] not in (None, "—") and last["pct"] > 0:
            st.session_state.mat_rows += 1
            _ensure_row(st.session_state.mat_rows - 1)
            st.rerun()

    # If total >= 100 → trim extra rows visually
    if running_total >= 100 and st.session_state.mat_rows > len(valid_rows):
        st.session_state.mat_rows = len(valid_rows)

    selected_materials = [r["mat"] for r in valid_rows]

    # Cotton flag
    cotton_value = ""
    if len(valid_rows) == 1:
        mat0 = (valid_rows[0]["mat"] or "").strip().lower()
        try:
            pct0_int = int(valid_rows[0]["pct"])
        except Exception:
            pct0_int = 0

        if mat0 == "cotton" and pct0_int == 100:
            cotton_value = "Z"

    # Info about totals
    if st.session_state.mat_rows == 1 and valid_rows and valid_rows[0]["pct"] == 100 and (
        valid_rows[0]["mat"] or ""
    ).lower() == "cotton":
        st.info("✅ 100% selected")
    elif running_total > 100:
        st.error("⚠️ Total exceeds 100%")

    st.write(f"**Total: {running_total}%**")

    # ============================================================
    #  Material Translation for AL / MK
    # ============================================================
    material_trans_dict = {}
    material_compositions = {}

    if selected_materials and not material_translations_df.empty:
        for lang in ['AL', 'MK']:
            names = []
            comp = []

            for r in valid_rows:
                t = material_translations_df[
                    (material_translations_df['material'] == r['mat']) &
                    (material_translations_df['language'] == lang)
                ]
                if not t.empty:
                    tr = t['translation'].iloc[0]
                    names.append(tr)
                    comp.append(f"{r['pct']}% {tr}")

            if names:
                material_trans_dict[lang] = ", ".join(names)
            if comp:
                material_compositions[lang] = ", ".join(comp)

    # ============================================================
    #  DataFrame enrichment (Dept, Cotton, Collection, Product, Washing)
    # ============================================================
    df['Dept'] = df['Item_classification'].apply(get_dept_value)

    if cotton_value == "Z":
        df['Cotton'] = cotton_value
    else:
        if 'Cotton' in df.columns:
            df = df.drop(columns=['Cotton'])

    df['Collection'] = df.apply(
        lambda r: modify_collection(r['Collection'], r['Item_classification']),
        axis=1
    )

    product_row = filtered[filtered['PRODUCT_NAME'] == product_type]
    if not product_row.empty:
        df['product_name'] = format_product_translations(
            product_type,
            product_row.iloc[0],
            selected_materials,
            material_trans_dict,
            material_compositions
        )
    else:
        df['product_name'] = ""

    df['washing_code'] = WASHING_CODES[washing_code_key]

    # ============================================================
    #  PRICE LADDER + CSV EXPORT
    # ============================================================
    if pln_price is not None:
        currency_values = find_closest_price(pln_price)

        if currency_values:
            # Fill currency columns
            for cur in ['EUR', 'BGN', 'BAM', 'RON', 'CZK', 'UAH', 'MKD', 'RSD', 'HUF']:
                df[cur] = currency_values.get(cur, "")

            df['PLN'] = format_number(pln_price, 'PLN')

            # NEW COLUMN → Item name English (cleaned & CAPITAL)
            df["Item_name_English"] = df["Item_name_EN"].apply(clean_item_name_english)

            final_cols = [
                "Order_ID", "Style", "Colour", "Supplier_product_code",
                "Item_classification", "Supplier_name", "today_date",
                "Collection", "Colour_SKU", "Style_Merch_Season",
                "Batch", "barcode", "washing_code", "EUR", "BGN",
                "BAM", "PLN", "RON", "CZK", "UAH", "MKD", "RSD", "HUF",
                "product_name", "Dept", "Item_name_English", "Season", "Sizes"
            ]

            # Optionally include Cotton column
            if 'Cotton' in df.columns and 'Cotton' not in final_cols:
                final_cols.append("Cotton")

            # Ensure all columns exist
            for col in final_cols:
                if col not in df.columns:
                    df[col] = ""

            st.success("✅ Done!")
            st.subheader("Edit Before Download")

            edited_df = st.data_editor(df[final_cols])

            # Build CSV with ; separator & quoted fields
            csv_buffer = StringIO()
            writer = pycsv.writer(
                csv_buffer,
                delimiter=';',
                quoting=pycsv.QUOTE_ALL
            )
            writer.writerow(final_cols)

            for row in edited_df.itertuples(index=False):
                writer.writerow(row)

            # ---------- Custom CSV filename ----------
            first_row_df = df.iloc[0]
            season_val = first_row_df.get("Season", "UNKNOWN").upper()

            all_skus = df['Colour_SKU'].apply(
                lambda x: re.sub(r".*SKU\s*", "", x)
            ).tolist()
            sku_val = "_".join(all_skus) if all_skus else "UNKNOWN"

            supplier_code = first_row_df.get("Supplier_product_code", "UNKNOWN")
            style_val = first_row_df.get("Style", "UNKNOWN")

            custom_filename = (
                f"PEPCO_{season_val}_{sku_val}_Swingtag "
                f"{supplier_code}_00_{style_val}.csv"
            )

            st.download_button(
                "📥 Download CSV",
                csv_buffer.getvalue().encode('utf-8-sig'),
                file_name=custom_filename,
                mime="text/csv"
            )
        else:
            st.warning("⚠️ Processing stopped - valid PLN price not found")


# ================================================================
#  PEPCO SECTION (Uploader + Reset)
# ================================================================
def pepco_section():
    """Main PEPCO UI section (upload + reset + extra order IDs merge)."""
    st.subheader("PEPCO Data Processing")

    # One-time init for uploader key
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0

    cols = st.columns([1, 6])

    # Reset / new upload button
    with cols[0]:
        def _reset_all():
            # Clear only app-related session keys
            for k in list(st.session_state.keys()):
                if k.startswith((
                    "ui_", "mat_", "pepco_",
                    "colour_", "colour_manual_", "colour_missing_"
                )):
                    st.session_state.pop(k, None)

            # Force uploader refresh
            st.session_state.uploader_key += 1
            # st.rerun() REMOVED (callback auto reruns)

        st.button("🆕 Upload New File", on_click=_reset_all)

    # File uploader (multi PDF)
    uploaded_pdfs = st.file_uploader(
        "Upload PEPCO Data file",
        type=["pdf"],
        key=f"pepco_uploader_{st.session_state.uploader_key}",
        accept_multiple_files=True
    )

    if uploaded_pdfs:
        if not isinstance(uploaded_pdfs, list):
            uploaded_pdfs = [uploaded_pdfs]

        primary_pdf = uploaded_pdfs[0]
        others = uploaded_pdfs[1:]

        # Collect Order_ID from additional PDFs
        other_ids = []
        for f in others:
            try:
                f.seek(0)
            except Exception:
                pass

            oid = extract_order_id_only(f)
            if oid:
                other_ids.append(oid)

            try:
                f.seek(0)
            except Exception:
                pass

        concatenated_ids = "+".join(other_ids) if other_ids else ""
        process_pepco_pdf(primary_pdf, extra_order_ids=concatenated_ids)


# ================================================================
#  MAIN APP
# ================================================================
def main():
    # Title
    st.title("PEPCO Automation App")

    # Main content
    pepco_section()

    st.markdown("---")
    st.caption("This app developed by Ovi")


# ================================================================
#  ENTRY POINT
# ================================================================
if __name__ == "__main__":
    main()
