"""
core/batch.py
=============
Batch (উৎপাদন মাস) আর label-এর "STYLE ... • Batch No./" লাইন (SS27 / app 1 থেকে)।

  Batch = Handover date - BATCH_OFFSET_DAYS (20 দিন) -> "MMYYYY"
          যেমন Handover 15/07/2026 -> 25/06/2026 -> "062026"
"""
import re
from datetime import datetime, timedelta

from core.config import BATCH_LABEL_PREFIX, BATCH_OFFSET_DAYS


def extract_batch(pages_text):
    """page 1-এর Handover date থেকে Batch ("MMYYYY")। না পেলে বা date ভুল হলে "UNKNOWN"।"""
    m = re.search(r"Handover\s*date\s*\.{2,}\s*(\d{2}/\d{2}/\d{4})", pages_text[0])
    if m:
        try:
            handover = datetime.strptime(m.group(1), "%d/%m/%Y")
            return (handover - timedelta(days=BATCH_OFFSET_DAYS)).strftime("%m%Y")
        except Exception:
            pass
    return "UNKNOWN"


def format_batch_label(batch):
    """SS27-এর Batch column: "виготовлення: 062026"।"""
    return f"{BATCH_LABEL_PREFIX}{batch}"


def build_style_merch_season(style_code, merch_code, season_yy):
    """
    SS27-এর Style_Merch_Season column:
      "STYLE 123456 • AB/CD27 • Batch No./"
    style না পেলে "STYLE UNKNOWN"; merch না পেলে মাঝের অংশ ফাঁকা।
    (merch_code / season_yy আসে extract_header_fields() থেকে)
    """
    if not style_code or style_code == "UNKNOWN":
        return "STYLE UNKNOWN"

    suffix = f"{merch_code}{season_yy}" if merch_code else ""
    return f"STYLE {style_code} • {suffix} • Batch No./"
