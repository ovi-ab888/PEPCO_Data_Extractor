"""
PEPCO Data Extractor — main file
================================
এখানে শুধু import আর mode বাছাই। সব logic core/ আর modules/-এ।

নতুন mode যোগ করতে: modules/ এ file বানিয়ে render() লিখুন,
তারপর নিচের MODES-এ এক লাইন যোগ করুন।
"""
import streamlit as st

# set_page_config সবার আগে হতে হবে
st.set_page_config(page_title="PEPCO Data Extractor", page_icon="🧾", layout="wide")

from modules.basic_data import render as render_basic_data

MODES = {
    "📋 Basic Data": render_basic_data,
    # "🏷️ SS27 Sticker": render_ss27,
    # "📦 Label V3": render_label_v3,
    # "🧵 Care Label": render_care_label,
}


def main():
    st.title("PEPCO Data Extractor")

    if len(MODES) > 1:
        mode = st.sidebar.radio("Select Mode", list(MODES.keys()))
    else:
        mode = next(iter(MODES))

    MODES[mode]()

    st.markdown("---")
    st.caption("This app developed by Ovi")


if __name__ == "__main__":
    main()
