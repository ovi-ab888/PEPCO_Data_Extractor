"""
core/price.py
=============
Price-এর সব function ও logic এক জায়গায় (SS27 / app 1 থেকে)।

Flow:
  PDF   -> extract_pl_sales_price_from_pdf()  PLN price (text)
  UI    -> parse_pln_price()                  text -> float
  Sheet -> load_price_data()                  price ladder (Google Sheet)
        -> find_closest_price()               PLN-এর সাথে মিলিয়ে বাকি currency-র দাম
        -> add_price_columns()                DataFrame-এ EUR, BGN ... PLN column বসায়
"""
import re

import pandas as pd
import streamlit as st

from core.config import (
    CACHE_TTL,
    DECIMAL_CURRENCIES,
    PRICE_SHEET_URL,
    SS27_CURRENCY_COLUMNS,
)


# ================================================================
#  PRICE LADDER LOADER (Google Sheet)
# ================================================================
@st.cache_data(ttl=CACHE_TTL)
def load_price_data():
    """
    Price ladder → {currency: [values]}। Fail করলে None।

    সব column-এর row একই index-এ থাকে: PLN ফাঁকা row বাদ যায়, আর অন্য column-এর
    ফাঁকা cell "" হয় (আগে column-ভিত্তিক dropna হত, তাতে মাঝে ফাঁকা cell থাকলে
    পরের দামগুলো এক ঘর সরে যেত)।
    """
    try:
        df = pd.read_csv(PRICE_SHEET_URL)

        if df.empty:
            st.error("Price data sheet is empty")
            return None

        if "PLN" in df.columns:
            df = df.dropna(subset=["PLN"])

        df = df.astype(object).where(df.notna(), "")

        return {cur: df[cur].tolist() for cur in df.columns}

    except Exception as e:
        st.error(f"Failed to load price data: {str(e)}")
        return None


# ================================================================
#  PL SALES PRICE FROM PDF
# ================================================================
def extract_pl_sales_price_from_pdf(pages_text):
    """PDF-এর "PL" লাইন (বা তার পরের ৪ লাইন) থেকে PL Sales Price ("12.50")। না পেলে ""।"""
    for text in pages_text:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for idx, line in enumerate(lines):
            if line == "PL" or line.startswith("PL "):
                # আগে একই লাইনে খুঁজি
                prices = re.findall(r"\b\d+(?:[.,]\d{2})\b", line)
                if prices:
                    return prices[0].replace(",", ".")

                # না পেলে পরের কয়েক লাইনে
                for next_line in lines[idx + 1:idx + 5]:
                    prices = re.findall(r"\b\d+(?:[.,]\d{2})\b", next_line)
                    if prices:
                        return prices[0].replace(",", ".")
    return ""


# ================================================================
#  PLN INPUT PARSER (UI text -> float)
# ================================================================
def parse_pln_price(raw):
    """
    "12.50" / "12,50" → 12.5। ফাঁকা হলে None (কোনো message ছাড়া)।
    ভুল বা negative হলে error দেখিয়ে None।
    """
    if not raw or not str(raw).strip():
        return None

    try:
        value = float(str(raw).replace(",", "."))
    except ValueError:
        st.error("❌ Please enter a valid number like 12.50 or 12,50")
        return None

    if value < 0:
        st.error("❌ Price can't be negative.")
        return None

    return value


# ================================================================
#  NUMBER FORMAT
# ================================================================
def format_number(value, currency):
    """
    Currency অনুযায়ী দাম format:
      EUR, BGN, BAM, RON, PLN -> দুই decimal, comma (12,50)
      বাকি (CZK, HUF ...)      -> পূর্ণ সংখ্যা (79)
    """
    try:
        if isinstance(value, str):
            value = float(value.replace(',', '.'))

        if currency in DECIMAL_CURRENCIES:
            return f"{float(value):.2f}".replace(".", ",")

        return str(int(float(value)))

    except (ValueError, TypeError):
        return str(value)


# ================================================================
#  PRICE LADDER LOOKUP
# ================================================================
def find_closest_price(pln_value):
    """
    PLN দাম ladder-এ খুঁজে বাকি currency-র দাম ফেরত দেয়:
      {"EUR": "2,50", "CZK": "59", ...}
    (নামে closest, কিন্তু আসলে হুবহু মিল লাগে — না মিললে error দেখিয়ে None)
    """
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


# ================================================================
#  DATAFRAME-এ PRICE COLUMN বসানো
# ================================================================
def add_price_columns(df, pln_price):
    """
    df-এ EUR, BGN, BAM, RON, CZK, UAH, MKD, RSD, HUF আর PLN column বসায়।
    Return: df; pln_price None হলে None (কিছু দেখায় না); ladder-এ না মিললে warning দিয়ে None।
    """
    if pln_price is None:
        return None

    currency_values = find_closest_price(pln_price)
    if not currency_values:
        st.warning("⚠️ Processing stopped - valid PLN price not found")
        return None

    for cur in SS27_CURRENCY_COLUMNS:
        df[cur] = currency_values.get(cur, "")

    df['PLN'] = format_number(pln_price, 'PLN')
    return df
