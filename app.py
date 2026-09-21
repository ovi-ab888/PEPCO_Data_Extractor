# ================================================================
# PART 1 — PAGE CONFIG + IMPORTS + CONSTANTS
# ================================================================

import streamlit as st
st.set_page_config(
    page_title="PEPCO SL",
    page_icon="🧾",
    layout="wide"
)

import fitz  # PyMuPDF
import pandas as pd
import re
from io import StringIO
import csv as pycsv
from datetime import datetime
import os


# ================================================================
# PICTOGRAM & PROMOTIONAL MAPPING
# ================================================================

PICTOGRAM_MAPPING = {
    "PIC00033": "A",
    "PIC00019": "8",
    "PIC00020": "9",
    "PIC00034": "B",
    "PIC00009": "R",
    "PIC00182": "3",
    "PIC00181": "5",
    "PIC00028": "S",
    "PIC00032": "C",
    "PIC00010": "Q",
    "PIC00178": "1",
    "PIC00014": "L",
    "PIC00011": "N",
    "PIC00183": "4",
    "PIC00186": "7",
    "PIC00184": "2",
    "PIC00012": "M",
    "PIC00031": "E",
    "PIC00029": "F",
    "PIC00027": "G",
    "PIC00185": "6",
    "PIC00013": "O",
    "PIC00180": "0",
    "PIC00030": "D",
}

PROMOTIONAL_MAPPING = {
    "PROMO": "P",
    "KVI": "K",
    "HS": "H",
}


# ================================================================
#  EXTRACTION FUNCTIONS
# ================================================================

def extract_all_tc_numbers_from_page4_plus(pages_text):
    """Extract ALL TC numbers ONLY from PAGE 4 and onwards. Max 7 unique."""
    tc_list = []
    
    if len(pages_text) >= 4:
        for i in range(3, len(pages_text)):
            page_text = pages_text[i]
            
            patterns = [
                r"TC\s*-\s*(T\d+)",
                r"TC\s*[:.]?\s*(T\d+)"
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text, re.IGNORECASE)
                for m in matches:
                    if m not in tc_list:
                        tc_list.append(m)
    
    return tc_list[:7]


def extract_all_barcodes_from_page4_plus(pages_text):
    """Extract ALL barcodes (13 digits) ONLY from PAGE 4 and onwards. Max 7 unique."""
    barcode_list = []
    
    if len(pages_text) >= 4:
        for i in range(3, len(pages_text)):
            page_text = pages_text[i]
            barcodes_on_page = re.findall(r"\b\d{13}\b", page_text)
            barcode_list.extend(barcodes_on_page)
    
    unique_barcodes = []
    for b in barcode_list:
        if b not in unique_barcodes:
            unique_barcodes.append(b)
    
    return unique_barcodes[:7]


def extract_product_name_from_page4_plus(pages_text):
    """Extract product name ONLY from PAGE 4 and onwards."""
    if len(pages_text) >= 4:
        for i in range(3, len(pages_text)):
            text = pages_text[i]
            m = re.search(r"ITEM\s*\d+\s*\n\s*(.+)", text, re.IGNORECASE)
            if not m:
                m = re.search(r"Product\s*name\s*[:.]?\s*(.+)", text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
    return ""


def extract_inner_kg_from_page4_plus(pages_text):
    """Extract inner kg ONLY from PAGE 4 and onwards."""
    if len(pages_text) >= 4:
        for i in range(3, len(pages_text)):
            text = pages_text[i]
            m = re.search(r"MAX\.?\s*(\d+)\s*kg", text, re.IGNORECASE)
            if not m:
                m = re.search(r"(\d+)\s*kg", text, re.IGNORECASE)
            if m:
                return f"MAX. {m.group(1)} kg"
    return ""


def extract_season_from_page4_plus(pages_text):
    """Extract season code ONLY from PAGE 4 and onwards."""
    if len(pages_text) >= 4:
        for i in range(3, len(pages_text)):
            text = pages_text[i]
            m = re.search(r"\b(AW|SS|FW|SW)\d{2}\b", text, re.IGNORECASE)
            if m:
                return m.group(0).upper()
    return ""


def extract_inner_qty_from_page4_plus(pages_text):
    """Extract inner quantity ONLY from PAGE 4 and onwards."""
    if len(pages_text) >= 4:
        for i in range(3, len(pages_text)):
            text = pages_text[i]
            m = re.search(r"(\d+)\s*Pcs", text, re.IGNORECASE)
            if m:
                return f"{m.group(1)} Pcs"
    return ""


def extract_outer_qty_from_page4_plus(pages_text):
    """Extract outer quantity ONLY from PAGE 4 and onwards."""
    if len(pages_text) >= 4:
        patterns = [
            r"(\d+)\s*Inner\s*OUTER",
            r"(\d+)\s*OUTER",
            r"OUTER\s*[:.]?\s*(\d+)",
            r"(\d+)\s*X\s*INNER\s*OUTER",
            r"OUTER\s*QTY\s*[:.]?\s*(\d+)"
        ]
        for i in range(3, len(pages_text)):
            text = pages_text[i]
            for p in patterns:
                m = re.search(p, text, re.IGNORECASE)
                if m:
                    return f"{m.group(1)} Inner"
    return ""


# ================================================================
#  MAIN PDF EXTRACTION ENGINE
# ================================================================

def extract_data_from_pdf(file):
    """Main PDF extractor - only required fields."""
    try:
        raw = file.read()
        if not raw:
            st.error("Empty PDF uploaded.")
            return None
        
        doc = fitz.open(stream=raw, filetype="pdf")
        
        if len(doc) < 1:
            st.error("PDF must have at least 1 page.")
            return None
        
        pages_text = [doc[i].get_text() for i in range(len(doc))]
        page1 = pages_text[0]
        
        # Extract from page 4 onwards
        all_tc_numbers = extract_all_tc_numbers_from_page4_plus(pages_text)
        all_barcodes = extract_all_barcodes_from_page4_plus(pages_text)
        
        product_name = extract_product_name_from_page4_plus(pages_text)
        inner_kg = extract_inner_kg_from_page4_plus(pages_text)
        season_st = extract_season_from_page4_plus(pages_text)
        inner_qty = extract_inner_qty_from_page4_plus(pages_text)
        outer_qty = extract_outer_qty_from_page4_plus(pages_text)
        
        # Pictogram
        pictogram = ""
        m = re.search(
            r"Pictogram\s*no.*?(PIC\d{5})",
            page1,
            re.IGNORECASE | re.DOTALL
        )
        if m:
            pictogram = PICTOGRAM_MAPPING.get(m.group(1).upper(), "")
        
        # Promotional
        promotional = " "
        m = re.search(
            r"Promotional\s*product.*?(NON\s+PROMO|PROMO|KVI|HS)\b",
            page1,
            re.IGNORECASE | re.DOTALL
        )
        if m:
            value = re.sub(r"\s+", " ", m.group(1).strip()).upper()
            if value == "NON PROMO":
                promotional = ""
            else:
                promotional = PROMOTIONAL_MAPPING.get(value, "")
        
        # Build results
        row_data = {
            "Pictogram": pictogram,
            "Promotional": promotional,
            "Product_name": product_name,
            "Inner_kg": inner_kg,
            "Season_st": season_st,
            "Inner_qty": inner_qty,
            "Outer_qty": outer_qty,
        }
        
        # Add TC numbers (st1 to st7)
        for i in range(7):
            col_name = f"TC_Number_st{i+1}"
            row_data[col_name] = all_tc_numbers[i] if i < len(all_tc_numbers) else ""
        
        # Add Barcodes (st1 to st7)
        for i in range(7):
            col_name = f"Barcode_st{i+1}"
            row_data[col_name] = all_barcodes[i] if i < len(all_barcodes) else ""
        
        return [row_data]
    
    except Exception as e:
        st.error(f"PDF error: {str(e)}")
        return None


# ================================================================
#  MAIN PROCESSOR FUNCTION
# ================================================================

def process_pepco_pdf(uploaded_pdf):
    """Main pipeline: parse PDF, build DF, export CSV."""
    
    if not uploaded_pdf:
        return
    
    result_data = extract_data_from_pdf(uploaded_pdf)
    if not result_data:
        return
    
    df = pd.DataFrame(result_data)
    
    # Final columns (only kept fields)
    final_cols = [
        "Pictogram",
        "Promotional",
        "Product_name",
        "Inner_kg",
        "Season_st",
        "Inner_qty",
        "Outer_qty"
    ]
    
    # Add TC Number columns
    tc_cols = [f"TC_Number_st{i+1}" for i in range(7)]
    for col in tc_cols:
        if col in df.columns:
            final_cols.append(col)
    
    # Add Barcode columns
    barcode_cols = [f"Barcode_st{i+1}" for i in range(7)]
    for col in barcode_cols:
        if col in df.columns:
            final_cols.append(col)
    
    # Ensure all columns exist
    for col in final_cols:
        if col not in df.columns:
            df[col] = ""
    
    st.success("✅ Done!")
    st.subheader("Edit Before Download")
    
    edited_df = st.data_editor(df[final_cols])
    
    # Build CSV
    csv_buffer = StringIO()
    writer = pycsv.writer(csv_buffer, delimiter=';', quoting=pycsv.QUOTE_ALL)
    writer.writerow(final_cols)
    
    for row in edited_df.itertuples(index=False):
        writer.writerow(row)
    
    # Simple filename
    custom_filename = f"PEPCO_Extracted_{datetime.today().strftime('%Y%m%d_%H%M%S')}.csv"
    
    st.download_button(
        "📥 Download CSV",
        csv_buffer.getvalue().encode('utf-8-sig'),
        file_name=custom_filename,
        mime="text/csv"
    )


# ================================================================
#  PEPCO SECTION
# ================================================================

def pepco_section():
    """Main PEPCO UI section."""
    st.subheader("PEPCO Data Processing")
    
    if "uploader_key" not in st.session_state:
        st.session_state.uploader_key = 0
    
    cols = st.columns([1, 6])
    
    with cols[0]:
        def _reset_all():
            st.session_state.uploader_key += 1
        
        st.button("🆕 Upload New File", on_click=_reset_all)
    
    uploaded_pdf = st.file_uploader(
        "Upload PEPCO Data file",
        type=["pdf"],
        key=f"pepco_uploader_{st.session_state.uploader_key}",
        accept_multiple_files=False
    )
    
    if uploaded_pdf:
        process_pepco_pdf(uploaded_pdf)


# ================================================================
#  MAIN APP
# ================================================================

def main():
    st.title("PEPCO Automation App")
    pepco_section()
    st.markdown("---")
    st.caption("This app developed by Ovi")


if __name__ == "__main__":
    main()
