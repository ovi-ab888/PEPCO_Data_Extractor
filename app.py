"""
PEPCO Data Extractor — main file
================================
এখানে শুধু page config আর title। সব logic core/ আর modules/extractor.py-তে।
"""
import streamlit as st

# set_page_config সবার আগে হতে হবে
st.set_page_config(page_title="PEPCO Data Extractor", page_icon="🧾", layout="wide")

from modules.extractor import render


def main():
    st.title("PEPCO Data Extractor")
    render()
    st.markdown("---")
    st.caption("This app developed by Ovi")


if __name__ == "__main__":
    main()
