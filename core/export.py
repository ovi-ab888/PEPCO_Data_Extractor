"""
core/export.py
==============
CSV তৈরির code (তিনটা app-এ একই ছিল): ; separator, সব field quoted, Excel-এর জন্য utf-8-sig।
"""
import csv
from io import StringIO

from core.config import CSV_DELIMITER


def build_csv_bytes(columns, df):
    """DataFrame → download_button-এ দেওয়ার মতো CSV bytes (utf-8-sig)।"""
    buf = StringIO()
    writer = csv.writer(buf, delimiter=CSV_DELIMITER, quoting=csv.QUOTE_ALL)
    writer.writerow(columns)
    for row in df[columns].itertuples(index=False):
        writer.writerow(row)
    return buf.getvalue().encode("utf-8-sig")
