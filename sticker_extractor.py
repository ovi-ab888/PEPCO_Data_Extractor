# ================================================================
#  sticker_extractor.py
#  Sticker data (sticker.py / PEPCO SL app-er logic) PDF theke extract kora.
#  Page 4 ar tar por theke: TC number, barcode, product name, kg, season, qty
#  Page 1 theke: Pictogram, Promotional
#
#  pdf_extractor.py te use hoy:
#      from sticker_extractor import extract_sticker_data, sticker_values_for_row
# ================================================================
import re

from constants import PICTOGRAM_MAPPING, PROMOTIONAL_MAPPING


# ================================================================
#  EXTRACTION FUNCTIONS (page 4+)  --  sticker.py theke hubuho
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
#  Ekshathe shob sticker data extract kore (1-ta dict)
#  Return keys:
#     pictogram, promotional, product_name, inner_kg, season_st,
#     inner_qty, outer_qty  -> single value (shob row te same)
#     tc_numbers, barcodes  -> list (row-er serial onujayi boshe)
# ================================================================
def extract_sticker_data(pages_text):
    page1 = pages_text[0] if pages_text else ""

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


    return {
        "pictogram": pictogram,
        "promotional": promotional,
        "product_name": product_name,
        "inner_kg": inner_kg,
        "season_st": season_st,
        "inner_qty": inner_qty,
        "outer_qty": outer_qty,
        "tc_numbers": all_tc_numbers,
        "barcodes": all_barcodes,
    }


# ================================================================
#  Ekta list theke N-th row-er value ber kora.
#  - list-e 1-ta item thakle -> shob row-e shei ekta-i (repeat)
#  - list-e 1-er beshi thakle -> N-th row-e N-th item (na thakle khali)
#  - list khali thakle -> shob row-e khali
# ================================================================
def _pick(values, idx):
    if len(values) == 1:
        return values[0]
    if idx < len(values):
        return values[idx]
    return ""


# ================================================================
#  N-th row er jonno 9-ta sticker column er value
#  TC_Number_st / Barcode_st: PDF-e 1-ta thakle shob row-e shei ekta-i
#  boshbe; joto size totota TC/Barcode thakle N-th row-e N-th ta boshbe.
# ================================================================
def sticker_values_for_row(sticker, idx):
    return {
        "Pictogram": sticker["pictogram"],
        "Promotional": sticker["promotional"],
        "Product_name_st": sticker["product_name"],
        "Inner_kg": sticker["inner_kg"],
        "Season_st": sticker["season_st"],
        "Inner_qty": sticker["inner_qty"],
        "Outer_qty": sticker["outer_qty"],
        "TC_Number_st": _pick(sticker["tc_numbers"], idx),
        "Barcode_st": _pick(sticker["barcodes"], idx),
    }
