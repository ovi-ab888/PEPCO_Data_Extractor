import streamlit as st
st.set_page_config(page_title="PEPCO Data Extractor", page_icon="🧾", layout="wide")

from core.theme import THEME_CSS, render_header
from core.auth import check_password
from modules.ss27.ui import render as render_ss27
from modules.label_v3.ui import render as render_v3
from modules.care_label.ui import render as render_care

MODES = {
    "🏷️ SS27 Sticker": render_ss27,
    "📦 Label V3": render_v3,
    "🧵 Care Label": render_care,
}

def main():
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    render_header()
    st.title("PEPCO Data Extractor")
    if not check_password():
        st.stop()
    mode = st.sidebar.radio("Select Mode", list(MODES.keys()))
    MODES[mode]()
    st.markdown("---")
    st.caption("This app developed by Ovi")

if __name__ == "__main__":
    main()
