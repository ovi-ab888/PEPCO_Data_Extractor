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
BATCH_LABEL_PREFIX = "виготовлення: "   # label-এ Batch-এর আগে যে লেখা বসে
V3_START_PAGE_INDEX = 3      # Label V3: page 4 থেকে শুরু (0-based index)
V3_MAX_ITEMS = 7             # Label V3: max TC / Barcode (st1..st7)


# ================================================================
# SS27 OUTPUT SETTINGS
# ================================================================
CSV_DELIMITER = ';'
MAX_MATERIAL_ROWS = 5        # SS27: max material row (composition UI)

# যেসব currency-তে 2 decimal + comma format হবে (format_number)
DECIMAL_CURRENCIES = ['EUR', 'BGN', 'BAM', 'RON', 'PLN']

# PLN ছাড়া বাকি currency column (price ladder থেকে বসে)
SS27_CURRENCY_COLUMNS = ['EUR', 'BGN', 'BAM', 'RON', 'CZK', 'UAH', 'MKD', 'RSD', 'HUF']

SS27_FINAL_COLUMNS = [
    "Order_ID", "Style", "Colour", "Supplier_product_code",
    "Item_classification", "Supplier_name", "today_date",
    "Collection", "Colour_SKU", "Style_Merch_Season",
    "Batch", "barcode", "washing_code", "EUR", "BGN",
    "BAM", "PLN", "RON", "CZK", "UAH", "MKD", "RSD", "HUF",
    "product_name", "Dept", "Item_name_English", "Season", "Sizes",
]


# ================================================================
# LABEL V3 OUTPUT SETTINGS
# ================================================================
V3_BASE_COLUMNS = [
    "Order_ID", "Style", "Colour", "Supplier_product_code",
    "Item_classification", "Supplier_name", "today_date",
    "Item_name_English", "Season", "Pictogram", "Promotional",
    "Product_name", "Inner_kg", "Season_st", "Inner_qty", "Outer_qty",
]
# এর পরে TC_Number_st1..st7 আর Barcode_st1..st7 — core/inner_outer.py-র tc_barcode_columns() দেয় (V3_MAX_ITEMS)


# ================================================================
# ITEM NAME PREFIXES (clean_item_name_english)
# ================================================================
# Item_name_EN-এর শুরুতে এগুলো থাকলে কেটে বাদ যাবে (case-insensitive)। লম্বা phrase আগে বসাবেন।
# "xxxxx" placeholder — আসল prefix হলে এখানে বসান।
ITEM_NAME_PREFIXES_SS27 = ["xxxxx"]
ITEM_NAME_PREFIXES_V3 = [
    # "sport",  # পুরোনো V3 code-এ "SPORT" ছিল কিন্তু কখনো match করত না। চালু করতে # তুলে দিন।
    "xxxxx",
]


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
        "BFF’S CLUB": "COLLECTION_1",
        "LOVELY GIRL": "COLLECTION_2",
        "MEADOWLANDS": "COLLECTION_3",
        "EASTER ELEGANT": "COLLECTION_4",
        "HOT_COUNTRIES_Santorini": "COLLECTION_5",
        "READ_FRUITS": "COLLECTION_6",
        "SEA_SHELLL": "COLLECTION_7",
        "WILD_FOREST": "COLLECTION_7",
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


# ================================================================
# MATERIAL / COMPONENT TRANSLATION (loader fallback)
# ================================================================
MATERIAL_TRANSLATION_LANGS = ['AL', 'MK']

# Google Sheet load না হলে এটা ব্যবহার হবে (আগে SS27-এ শুধু Cotton ছিল, Care-এরটা পুরো — Care-এরটাই রাখা হয়েছে)
MATERIAL_TRANSLATION_FALLBACK = [
    {'material': 'Cotton', 'language': 'AL', 'translation': 'Pambuk'},
    {'material': 'Cotton', 'language': 'MK', 'translation': 'Памук'},
    {'material': 'Polyester', 'language': 'AL', 'translation': 'Poliester'},
    {'material': 'Polyester', 'language': 'MK', 'translation': 'Полиестер'},
    {'material': 'Elastane', 'language': 'AL', 'translation': 'Elastan'},
    {'material': 'Elastane', 'language': 'MK', 'translation': 'Еластан'},
]

COMPONENT_TRANSLATION_FALLBACK = {
    "EN": ["Main fabric", "Lining", "Pocket bag", "Trim", "Hood", "Collar", "Cuff"],
    "AL": ["Pëlhurë kryesore", "Llastik", "Thes me xhepa", "Shkurtim", "Kapuç", "Jakë", "Manshetë"],
    "BG": ["Основен плат", "Подплата", "Вътрешен джоб", "Подстригване", "Качулка", "Яка", "Маншет"],
}


# ================================================================
# CARE LABEL SETTINGS
# ================================================================
CARE_DEPARTMENT_OPTIONS = [
    "Baby Boy", "Baby Girl", "Boys", "Girls", "Women", "Mens",
    "Boys Nightwear", "Girls Nightwear", "Adult Nightwear",
]

CARE_DEFAULT_MATERIALS = ["Cotton", "Polyester", "Elastane", "Nylon", "Viscose", "Wool"]
CARE_DEFAULT_COMPONENTS = ["Main fabric", "Outer fabric", "Lining", "Pocket bag", "Collar", "Cuff"]
CARE_MAX_COMPONENTS = 5

CARE_FINAL_COLUMNS = [
    "Order_ID", "Style", "Colour", "Supplier_product_code", "Item_classification",
    "Supplier_name", "today_date",
    "barcode", "Size", "SKU_Name", "washing_code",
    "Season", "Composition_Care", "Dept",
]

# Composition_Care-এর ভেতরে section গুলোর মাঝের ফাঁকা লাইন (আগে 10টা "\n" ছিল)
CARE_SECTION_GAP = "\n" * 10

CARE_SHRINKAGE_LINE = "Skupljanje:  po dužini: 4%, po širini 4%"

CARE_ORIGIN_TEXT = """Made in Bangladesh/ Vendi i Origjinës: Bangladesh/ Произведено в Бангладеш/ Fabricado en Bangladesh/ Κατασκευάζεται στην Μπαγκλαντές/ Pagaminta Bangladeše/ Ražots Bangladešā/ Wyprodukowano w Bangladeszu/ Произведено во Бангладеш/ Proizvedeno u Bangladešu/ Zemlja izvoza: EU/ Виготовлено в Бангладеш.

Produced by/ Prodhuesi/ Производител/ Výrobce/ Hersteller/ Tootja/ Fabricante/
Fabricant/ Κατασκευαστής/ Proizvođač/ Gyártó/ Produttore/ Gamintojas/ Ražotājs/ Producent/ Producător/ Izdelovalec/ Výrobca/ Виробник:


Pepco Poland Sp. z o.o., ul. Strzeszyńska 73A, 60-479 Poznań Poland, klient@pepco.eu, NIP (NIF) 782-21-31-157.
Пепко Полска Сп. з o.o., ул. Стрзесзинска 73А, 60-479 Познан. Пепко Польска Сп. з.о.о., вул Стшешинська 73A, 60-479 Познань. Na tržište RH stavlja: Pepco Croatia d.o.o., D. T. Gavrana 11, 10020 Zagreb.
Uvoznik za Srbiju: Pepco d.o.o., Pariske komune 22, 11070 Beograd-Novi Beograd. klijent.rs@pepco.eu
Διανομέας: Pepco Greece Μονοπρόσωπη Ι.Κ.Ε., Πέτρου Ράλλη 97, 182 33, Αγ. Ιωάννης Ρέντης. Uvoznik za BiH: Pepco B-H d.o.o., ulica Skenderpašina br. 1, Opština Centar Sarajevo, 71 000 Sarajevo. klijent.ba@pepco.eu
Увозник/ Importuesi: ПЕПЦО ДООЕЛ Скопје, Ул. НАУМ НАУМОВСКИ - БОРЧЕ Бр.40/5-8 СКОПЈЕ - ЦЕНТАР ЦЕНТАР/ PEPCO DOOEL Shkup, Rruga Naum Naumovski-Borche Nr. 40/5-8, Shkup – Qendër, Maqedonia e Veriut. Імпортер: ТОВАРИСТВО З ОБМЕЖЕНОЮ ВІДПОВІДАЛЬНІСТЮ “ПЕПКО УКРАЇНА” вул. Загородня, 15,
м. Київ, 03150, Україна, customer@pepco.eu"""


# ================================================================
# BASIC DATA MODE (শুধু header field — SS27 / app 1-এর logic)
# ================================================================
BASIC_DATA_COLUMNS = [
    "Order_ID", "Style", "Colour",
    "Supplier_product_code", "Item_classification", "Supplier_name",
    "Item_name_English", "Season", "Collection",
]


# ================================================================
# UNIFIED CSV (তিন app-এর সব column একটাই CSV-তে)
# ================================================================
CSV_FILENAME_TAG = "Data"   # file নাম: PEPCO_{season}_{skus}_{TAG} {supplier}_00_{style}.csv

UNIFIED_COLUMNS = (
    SS27_FINAL_COLUMNS                                             # SS27 (28)
    + ["Pictogram", "Promotional", "Product_name",                 # Label V3 (21)
       "Inner_kg", "Season_st", "Inner_qty", "Outer_qty"]
    + [f"TC_Number_st{i + 1}" for i in range(V3_MAX_ITEMS)]
    + [f"Barcode_st{i + 1}" for i in range(V3_MAX_ITEMS)]
    + ["SKU_Name"]                                                 # Care (এখন পর্যন্ত)
)
# এখনো নেই: Size, Composition_Care (Care), Cotton (SS27) — পরে যোগ হবে
