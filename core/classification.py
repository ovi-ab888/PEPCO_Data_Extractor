"""
core/classification.py
======================
Item_classification text থেকে type / department বের করার helper।
তিনটা app-এই ছিল; Care Label-এর version (Nightwear সহ) base ধরা হয়েছে।

Rule গুলো উপর থেকে নিচে check হয়, প্রথম match-ই জেতে।
"""

# (খোঁজার text, ফলাফল) — COLLECTION_MAPPING-এর key
_CLASSIFICATION_TYPE_RULES = [
    ('younger girls outerwear', 'yg'),
    ('older girls outerwear', 'og'),
    ('younger boys outerwear', 'yb'),
    ('older boys outerwear', 'ob'),
    ('baby girls outerwear', 'a'),
    ('baby boys outerwear', 'b'),
    ('baby girls essentials', 'd_girls'),
    ('baby boys essentials', 'd'),
    ('ladies outerwear', 'l'),
    ('mens outerwear', 'm'),
]

# (যেকোনো একটা text মিললেই, ফলাফল) — UI Department label
_DEPT_LABEL_RULES = [
    (('baby boys outerwear', 'baby boys essentials'), "Baby Boy"),
    (('baby girls outerwear', 'baby girls essentials'), "Baby Girl"),
    (('younger boys outerwear', 'older boys outerwear'), "Boys"),
    (('younger girls outerwear', 'older girls outerwear'), "Girls"),
    (('ladies outerwear',), "Women"),
    (('mens outerwear',), "Mens"),
    (('boys nightwear',), "Boys Nightwear"),
    (('girls nightwear',), "Girls Nightwear"),
    (('adult nightwear',), "Adult Nightwear"),
]

# (যেকোনো একটা text মিললেই, ফলাফল) — DEPT column (BABY / KIDS / TEENS ...)
_DEPT_VALUE_RULES = [
    (('baby boys', 'baby girls'), "BABY"),
    (('younger boys', 'younger girls'), "KIDS"),
    (('older girls', 'older boys'), "TEENS"),
    (('ladies outerwear',), "WOMEN"),
    (('mens outerwear',), "MEN"),
    (('boys nightwear', 'girls nightwear'), "KIDS"),
    (('adult nightwear',), "ADULT"),
]


def get_classification_type(item_class):
    """COLLECTION_MAPPING-এ যে key ব্যবহার হয় সেটা ফেরত দেয় (yg, og, yb ...)."""
    if not item_class:
        return None
    ic = item_class.lower()
    for needle, key in _CLASSIFICATION_TYPE_RULES:
        if needle in ic:
            return key
    return None


def map_item_class_to_dept_label(item_class):
    """UI Department name (Baby Boy, Girls, Women ...) ফেরত দেয়।"""
    if not item_class:
        return None
    ic = item_class.lower()
    for needles, label in _DEPT_LABEL_RULES:
        if any(n in ic for n in needles):
            return label
    return None


def get_dept_value(item_class):
    """DEPT column value: BABY / KIDS / TEENS / WOMEN / MEN / ADULT."""
    if not item_class:
        return ""
    ic = item_class.lower()
    for needles, value in _DEPT_VALUE_RULES:
        if any(n in ic for n in needles):
            return value
    return ""
