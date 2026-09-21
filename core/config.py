"""
core/config.py
==============
সব constant, mapping আর Google Sheet URL এক জায়গায়।
এই file-এ কোনো streamlit / logic code থাকবে না।

Source:
  - SS27          -> WASHING_CODES, COLLECTION_MAPPING, price/translation sheet,
                     COUNTRY_SUFFIXES, LANGUAGE_ORDER, BATCH_OFFSET_DAYS
  - Label V3      -> PICTOGRAM_MAPPING, PROMOTIONAL_MAPPING, V3_* limits
  - Care Label    -> CARE_SHEET_BASE_URL, CARE_SHEET_GIDS, WASHING_CODES
"""

# ================================================================
# GENERAL
# ================================================================
CACHE_TTL = 600  # seconds (Google Sheet cache)

DEFAULT_WASHING_CODE = "9"

WASHING_CODES = {
    '1': '১২৩৪৫', '2': '১৪৭৮৫', '3': 'djnst', '4': 'djnpt', '5': 'djnqt',
    '6': 'djnqt', '7': 'gjnpt', '8': 'gjnpu', '9': 'gjnqt', '10': 'gjnqu',
    '11': 'ijnst', '12': 'ijnsu', '13': 'ijnpu', '14': 'ijnsv', '15': 'djnsw'
}


# ================================================================
# GOOGLE SHEET URLS
# ================================================================
# --- Price ladder (SS27) ---
PRICE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRdAQmBHwDEWCgmLdEdJc0HsFYpPSyERPHLwmr2tnTYU1BDWdBD6I0ZYfEDzataX0wTNhfLfnm-Te6w/"
    "pub?gid=583402611&single=true&output=csv"
)

# --- Material translations AL / MK (SS27 + Care) ---
MATERIAL_TRANSLATION_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vRdAQmBHwDEWCgmLdEdJc0HsFYpPSyERPHLwmr2tnTYU1BDWdBD6I0ZYfEDzataX0wTNhfLfnm-Te6w/"
    "pub?gid=1096440227&single=true&output=csv"
)

# --- Product name translations (SS27) ---
PRODUCT_TRANSLATION_SHEET_ID = "1ue68TSJQQedKa7sVBB4syOc0OXJNaLS7p9vSnV52mKA"
PRODUCT_TRANSLATION_SHEET_NAME = "SS26 Product_Name"

# --- Care label & composition sheets (Care Label) ---
CARE_SHEET_BASE_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQtV5x4B3Sf_CCIMLCfvPtSP8nYru5BMAh5Xe4wWkqcrzZqT2cRJ7JYlvaHrsXql0h9Dnqohvq2mrKM/pub"
)

# key -> (gid, display name)
CARE_SHEET_GIDS = {
    "comp_instructions": ("0", "Composition Instructions"),
    "materials":         ("1935147264", "Materials"),
    "care_instructions": ("21483732", "Care Instructions"),
    "component_names":   ("0", "Component Names"),
}


# ================================================================
# PDF EXTRACTION SETTINGS
# ================================================================
BATCH_OFFSET_DAYS = 20       # SS27: Batch = Handover date - 20 days
V3_START_PAGE_INDEX = 3      # Label V3: page 4 থেকে শুরু (0-based index)
V3_MAX_ITEMS = 7             # Label V3: max TC / Barcode (st1..st7)


# ================================================================
# PICTOGRAM & PROMOTIONAL (Label V3)
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
# COLLECTION MAPPING (SS27)
# ================================================================
COLLECTION_MAPPING = {

    # ---------------- Baby Girls ----------------
    "a": {  # baby girls outerwear
        "CUTE BEAR": "MODERN 1",
        "SUMMER CHERRY": "ROMANTIC 1",
        "AUTUMN": "ROMANTIC 2",
    },
    "d_girls": {  # baby girls essentials
        "FLOWER MOUSE": "MODERN 1",
        "LITTEL FOREST": "ROMANTIC 1",
    },

    # ---------------- Baby Boys ----------------
    "b": {  # baby boys outerwear
        "DOGS&FRIENDS": "MODERN 1",
        "EXPOLORE THE MOUNTINE": "MODERN 2",
        "SUMMER FUN": "MODERN 4",
        "COOL TRIP": "CLASSIC 1",
        "COLLEGE BEARS": "CLASSIC 1",
    },
    "d": {  # baby boys essentials
        "DOGS FRIENDS": "CLASSIC 1",
        "FOREST STORY": "MODERN 1",
        "LITTLE DREAMER": "MODERN 1",
        "X-MAS": "CLASSIC 2",
    },

    # ---------------- Younger Girls ----------------
    "yg": {  # younger girls outerwear
        "PONNY_RAINBOW": "COLLECTION 1",
        "MEOW_STORY": "COLLECTION 2",
        "BTS": "COLLECTION 3",
        "COZY AUTUMN": "COLLECTION 4",
        "WINTER BALLET": "COLLECTION 5",
        "XMAS": "COLLECTION 6",
        "PARTY": "COLLECTION 7",
    },

    # ---------------- Older Girls ----------------
    "og": {  # older girls outerwear
        "xxxxx": "COLLECTION_0",
        "TRANSITIONAL LUMINOUS BLUME": "COLLECTION 1",
        "VALENTINE": "COLLECTION 2",
        "SOUVENIRE SNACK": "COLLECTION 3",
        "MY FAVOURITE THINGS": "COLLECTION 4",
        "CANDY": "COLLECTION 5",
        "SEASIDE": "COLLECTION 6",
        "LE SOLEI": "COLLECTION 7",
        "xxxxx": "COLLECTION 0",
    },

    # ---------------- Younger Boys ----------------
    "yb": {  # younger boys outerwear
        "FUNDAY CLUB": "COLLECTION_1",
        "DISCOVER DINO": "COLLECTION_2",
        "DOUBLE-TAKE": "COLLECTION_3",
        "EASTER ELEGANT": "COLLECTION_4",
        "SPORT": "COLLECTION_5",
        "MARITIME": "COLLECTION_6",
        "JUNGLE VIBES": "COLLECTION_7",
        "SURFING": "COLLECTION_8",
    },

    # ---------------- Older Boys ----------------
    "ob": {  # older boys outerwear
        "REBEL RIDER": "COLLECTION 1",
        "SKATE EPIC": "COLLECTION 2",
        "GAMER MODE": "COLLECTION 3",
        "SPORT": "COLLECTION 4",
        "SURFING": "COLLECTION 5",
    },

    # ---------------- Ladies ----------------
    "l": {  # ladies outerwear
        "XXXXX_1": "COLLECTION_1",
        "XXXXX_2": "COLLECTION_2",
        "XXXXX_3": "COLLECTION_3",
        "XXXXX_4": "COLLECTION_4",
        "XXXXX_5": "COLLECTION_5",
    },

    # ---------------- Mens ----------------
    "m": {  # mens outerwear
        "XXXXX_1": "COLLECTION_1",
        "XXXXX_2": "COLLECTION_2",
        "XXXXX_3": "COLLECTION_3",
        "XXXXX_4": "COLLECTION_4",
        "XXXXX_5": "COLLECTION_5",
    },
}


# ================================================================
# PRODUCT TRANSLATION SETTINGS (SS27)
# ================================================================
# Country অনুযায়ী translation-এর শেষে যে suffix বসবে
COUNTRY_SUFFIXES = {
    'BiH': " Sastav materijala na ušivenoj etiketi.",
    'RS': " Sastav materijala nalazi se na ušivenoj etiketi.",
    'UA': (
        " Імпортер приймає претензії. Термін придатності – необмежений, "
        "якщо продукт використовується за призначенням (якщо на упаковці "
        "або продукті не вказано термін придатності). Умови зберігання – "
        "Зберігати в сухому місці при кімнатній температурі."
    ),
}

# Translation output-এর language order (EN আলাদা, সবার আগে বসে)
LANGUAGE_ORDER = [
    'AL', 'BG', 'BiH', 'CZ', 'DE', 'EE',
    'ES', 'GR', 'HR', 'HU', 'IT', 'LT',
    'LV', 'MK', 'PL', 'PT', 'RO', 'RS',
    'SI', 'SK', 'UA'
]
