# ================================================================
# PEPCO Automation App - Minimal Version
# Only outputs: washing_code + Composition_Care
# ================================================================

import streamlit as st
st.set_page_config(
    page_title="PEPCO",
    page_icon="🧾",
    layout="wide"
)

import pandas as pd
from io import StringIO
import csv as pycsv
from datetime import datetime


# ================================================================
#  CONSTANTS
# ================================================================
WASHING_CODES = {
    '1': '১২৩৪৫', '2': '১৪৭৮৫', '3': 'djnst', '4': 'djnpt', '5': 'djnqt',
    '6': 'djnqt', '7': 'gjnpt', '8': 'gjnpu', '9': 'gjnqt', '10': 'gjnqu',
    '11': 'ijnst', '12': 'ijnsu', '13': 'ijnpu', '14': 'ijnsv', '15': 'djnsw'
}


# ================================================================
#  DATA LOADERS
# ================================================================
@st.cache_data(ttl=600)
def load_care_composition_data():
    BASE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQtV5x4B3Sf_CCIMLCfvPtSP8nYru5BMAh5Xe4wWkqcrzZqT2cRJ7JYlvaHrsXql0h9Dnqohvq2mrKM/pub"
    
    sheets_config = {
        "materials": {"url": f"{BASE_URL}?gid=1935147264&single=true&output=csv"},
        "care_instructions": {"url": f"{BASE_URL}?gid=21483732&single=true&output=csv"},
        "component_names": {"url": f"{BASE_URL}?gid=0&single=true&output=csv"}
    }
    
    result = {}
    for key, config in sheets_config.items():
        try:
            df = pd.read_csv(config["url"])
            result[key] = df if not df.empty else pd.DataFrame()
        except Exception:
            result[key] = pd.DataFrame()
    return result


@st.cache_data(ttl=600)
def load_component_translations():
    care_data = load_care_composition_data()
    if not care_data["component_names"].empty:
        return care_data["component_names"]
    return pd.DataFrame({
        "EN": ["Main fabric", "Lining", "Pocket bag", "Trim", "Hood", "Collar", "Cuff", "Rib"],
        "AL": ["Pëlhurë kryesore", "Llastik", "Thes me xhepa", "Shkurtim", "Kapuç", "Jakë", "Manshetë", "Rib"],
        "BG": ["Основен плат", "Подплата", "Вътрешен джоб", "Подстригване", "Качулка", "Яка", "Маншет", "Rib"]
    })


# ================================================================
#  MAIN PROCESSOR
# ================================================================
def process_pepco():
    care_data = load_care_composition_data()
    comp_translations_df = load_component_translations()

    # ---------- Washing Code ----------
    st.markdown("### 🧺 Washing Code")
    washing_options = list(WASHING_CODES.keys())
    washing_default_index = washing_options.index('9') if '9' in washing_options else 0
    washing_code_key = st.selectbox(
        "Select Washing Code",
        options=washing_options,
        index=washing_default_index,
        key="ui_wash"
    )
    washing_code = WASHING_CODES[washing_code_key]

    # ---------- Material Composition ----------
    st.markdown("### 🧵 Material Composition (%)")
    
    materials_df = care_data.get("materials", pd.DataFrame())
    
    materials_options = []
    if not materials_df.empty:
        en_col = materials_df.columns[0]
        materials_options = materials_df[en_col].dropna().astype(str).tolist()
    if not materials_options:
        materials_options = ["Cotton", "Polyester", "Elastane", "Nylon", "Viscose", "Wool"]
    
    component_options = []
    if not comp_translations_df.empty:
        component_options = comp_translations_df["EN"].dropna().astype(str).tolist()
    if not component_options:
        component_options = ["Main fabric", "Outer fabric", "Lining", "Pocket bag", "Collar", "Cuff", "Rib"]
    
    use_advanced_mode = st.toggle("🔧 Advanced Mode (Multiple Components)", value=False)
    
    if "composition_blocks" not in st.session_state:
        st.session_state.composition_blocks = []
    
    if not st.session_state.composition_blocks:
        st.session_state.composition_blocks.append({
            "component_name": "Main fabric",
            "component_name_optional": "",
            "materials": [{"mat": "", "pct": 0}]
        })
    
    def get_material_all_languages(mat_name, pct):
        if materials_df.empty or not mat_name:
            return f"{pct}% {mat_name}"
        en_col = materials_df.columns[0]
        row = materials_df[materials_df[en_col].astype(str).str.strip() == mat_name]
        if row.empty:
            return f"{pct}% {mat_name}"
        translations = [mat_name]
        for col in materials_df.columns:
            val = row.iloc[0].get(col, "")
            if pd.notna(val) and str(val).strip() and val != mat_name:
                text = str(val).strip()
                if text:
                    text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
                translations.append(text)
        return f"{pct}% {'/ '.join(translations)}"
    
    def get_component_name_translations(comp_name):
        if not comp_name or comp_translations_df.empty:
            return comp_name
        row = comp_translations_df[comp_translations_df['EN'].astype(str).str.strip() == comp_name]
        if row.empty:
            return comp_name
        translations = [comp_name]
        for col in comp_translations_df.columns:
            if col != 'EN':
                val = row.iloc[0].get(col, "")
                if pd.notna(val) and str(val).strip():
                    text = str(val).strip()
                    if text:
                        text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
                    translations.append(text)
        return "/ ".join(translations)
    
    def build_material_line(materials):
        parts = []
        for m in materials:
            if m["mat"] and m["pct"] > 0:
                mat_text = get_material_all_languages(m["mat"], m["pct"])
                if mat_text:
                    mat_text = mat_text[0].upper() + mat_text[1:] if len(mat_text) > 1 else mat_text.upper()
                parts.append(mat_text)
        return "\n\n".join(parts)
    
    components_data = []
    
    for block_idx, block in enumerate(st.session_state.composition_blocks):
        with st.container(border=True):
            top1, top2 = st.columns([5, 1])
            with top1:
                if use_advanced_mode:
                    # ===== Component Name + Optional Component Name (Same Line) =====
                    col_name1, col_name2 = st.columns(2)
                    
                    with col_name1:
                        current_name = block.get("component_name", "Main fabric")
                        name_index = component_options.index(current_name) if current_name in component_options else 0
                        block["component_name"] = st.selectbox(
                            f"Component Name #{block_idx + 1}",
                            options=component_options,
                            index=name_index,
                            key=f"comp_name_{block_idx}"
                        )
                    
                    with col_name2:
                        optional_options = [""] + component_options
                        current_optional = block.get("component_name_optional", "")
                        optional_index = optional_options.index(current_optional) if current_optional in optional_options else 0
                        block["component_name_optional"] = st.selectbox(
                            f"Optional Component Name #{block_idx + 1}",
                            options=optional_options,
                            index=optional_index,
                            key=f"comp_name_optional_{block_idx}"
                        )
                else:
                    st.markdown("#### Simple Composition")
            with top2:
                if len(st.session_state.composition_blocks) > 1:
                    st.write("")
                    st.write("")
                    if st.button("🗑️", key=f"remove_block_{block_idx}"):
                        st.session_state.composition_blocks.pop(block_idx)
                        st.rerun()
            
            st.markdown("#### Materials")
            for mat_idx, mat in enumerate(block["materials"]):
                c1, c2, c3 = st.columns([3, 1.5, 0.7])
                with c1:
                    mat_options = [""] + materials_options
                    mat_index = mat_options.index(mat["mat"]) if mat["mat"] in mat_options else 0
                    mat["mat"] = st.selectbox(
                        "Material",
                        options=mat_options,
                        index=mat_index,
                        key=f"mat_{block_idx}_{mat_idx}"
                    )
                with c2:
                    mat["pct"] = st.number_input(
                        "%",
                        min_value=0,
                        max_value=100,
                        step=1,
                        value=int(mat["pct"]),
                        key=f"pct_{block_idx}_{mat_idx}"
                    )
                with c3:
                    st.write("")
                    if len(block["materials"]) > 1:
                        if st.button("❌", key=f"remove_mat_{block_idx}_{mat_idx}"):
                            block["materials"].pop(mat_idx)
                            st.rerun()
            
            if st.button("➕ Add Material", key=f"add_material_{block_idx}"):
                block["materials"].append({"mat": "", "pct": 0})
                st.rerun()
            
            valid_materials = [m for m in block["materials"] if m["mat"] and m["pct"] > 0]
            total_pct = sum(m["pct"] for m in valid_materials)
            
            if total_pct == 100:
                st.success(f"✅ Total = {total_pct}%")
            elif total_pct < 100 and total_pct > 0:
                st.warning(f"⚠️ Remaining = {100 - total_pct}%")
            elif total_pct > 100:
                st.error(f"❌ Exceeded by {total_pct - 100}%")
            else:
                st.info("📌 Enter material composition")
            
            if valid_materials and total_pct == 100:
                components_data.append({
                    "name": block["component_name"],
                    "name_optional": block.get("component_name_optional", ""),
                    "materials": valid_materials.copy()
                })
    
    if use_advanced_mode:
        if len(st.session_state.composition_blocks) < 5:
            if st.button("➕ Add Component", key="add_component_btn"):
                st.session_state.composition_blocks.append({
                    "component_name": "Main fabric",
                    "component_name_optional": "",
                    "materials": [{"mat": "", "pct": 0}]
                })
                st.rerun()
        else:
            st.info("Maximum 5 components allowed")
    
    # Build composition text
    composition_lines = []
    for comp in components_data:
        material_text = build_material_line(comp["materials"])
        
        if use_advanced_mode:
            main_name = get_component_name_translations(comp["name"])
            optional_name = get_component_name_translations(comp["name_optional"]) if comp.get("name_optional") else ""
            
            if optional_name:
                line = f"{main_name}\n\n{optional_name}:\n\n{material_text}"
            else:
                line = f"{main_name}:\n\n{material_text}"
        else:
            line = material_text
        
        composition_lines.append(line)
    
    final_composition_text = "\n\n".join(composition_lines)

    # ---------- Care Instructions ----------
    st.markdown("### 🏷️ Care Instructions")
    
    care_instructions_df = care_data.get("care_instructions", pd.DataFrame())
    
    if "care_inst_list" not in st.session_state:
        st.session_state.care_inst_list = []
    
    care_inst_options = []
    if not care_instructions_df.empty:
        en_col = care_instructions_df.columns[0]
        care_inst_options = care_instructions_df[en_col].dropna().astype(str).tolist()
    
    if st.session_state.care_inst_list:
        st.write("**Selected Care Instructions:**")
        for idx, selected in enumerate(st.session_state.care_inst_list):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"• {selected}")
            with col2:
                if st.button("Remove", key=f"remove_care_{idx}"):
                    st.session_state.care_inst_list.pop(idx)
                    st.rerun()
    
    col_add_care, _ = st.columns([2, 3])
    with col_add_care:
        new_care_inst = st.selectbox("Add Care Instruction", options=[""] + care_inst_options, key="new_care_inst_select")
        if st.button("Add Care Instruction", key="add_care_inst_btn"):
            if new_care_inst and new_care_inst not in st.session_state.care_inst_list:
                st.session_state.care_inst_list.append(new_care_inst)
                st.rerun()
            elif new_care_inst in st.session_state.care_inst_list:
                st.warning("This instruction already added!")
    
    def get_care_instruction_all_languages(inst_text, care_instructions_df):
        if not inst_text or care_instructions_df.empty:
            return ""
        en_col = care_instructions_df.columns[0]
        row = care_instructions_df[care_instructions_df[en_col].astype(str).str.strip() == inst_text]
        if row.empty:
            return ""
        translations = []
        for col in care_instructions_df.columns:
            val = row.iloc[0].get(col, "")
            if pd.notna(val) and str(val).strip():
                text = str(val).strip()
                if text:
                    text = text[0].upper() + text[1:] if len(text) > 1 else text.upper()
                translations.append(text)
        return "/ ".join(translations)
    
    all_care_inst_translated = []
    for selected_care_inst in st.session_state.care_inst_list:
        inst_text = get_care_instruction_all_languages(selected_care_inst, care_instructions_df)
        if inst_text:
            all_care_inst_translated.append(inst_text)
    
    care_inst_translated = "\n\n".join(all_care_inst_translated) if all_care_inst_translated else ""

    # ---------- Build Composition_Care ----------
    combined_care = ""
    if final_composition_text and care_inst_translated:
        combined_care = f"{final_composition_text}\n\n\n{care_inst_translated}"
    elif final_composition_text:
        combined_care = final_composition_text
    elif care_inst_translated:
        combined_care = care_inst_translated

    shrinkage_line = "Skupljanje:  po dužini: 4%, po širini 4%"

    bangladesh_line = """Made in Bangladesh/ Vendi i Origjinës: Bangladesh/ Произведено в Бангладеш/ Fabricado en Bangladesh/ Κατασκευάζεται στην Μπαγκλαντές/ Pagaminta Bangladeše/ Ražots Bangladešā/ Wyprodukowano w Bangladeszu/ Произведено во Бангладеш/ Proizvedeno u Bangladešu/ Zemlja izvoza: EU/ Виготовлено в Бангладеш.

Produced by/ Prodhuesi/ Производител/ Výrobce/ Hersteller/ Tootja/ Fabricante/
Fabricant/ Κατασκευαστής/ Proizvođač/ Gyártó/ Produttore/ Gamintojas/ Ražotājs/ Producent/ Producător/ Izdelovalec/ Výrobca/ Виробник:


Pepco Poland Sp. z o.o., ul. Strzeszyńska 73A, 60-479 Poznań Poland, klient@pepco.eu, NIP (NIF) 782-21-31-157.
Пепко Полска Сп. з o.o., ул. Стрзесзинска 73А, 60-479 Познан. Пепко Польска Сп. з.о.о., вул Стшешинська 73A, 60-479 Познань. Na tržište RH stavlja: Pepco Croatia d.o.o., D. T. Gavrana 11, 10020 Zagreb.
Uvoznik za Srbiju: Pepco d.o.o., Pariske komune 22, 11070 Beograd-Novi Beograd. klijent.rs@pepco.eu
Διανομέας: Pepco Greece Μονοπρόσωπη Ι.Κ.Ε., Πέτρου Ράλλη 97, 182 33, Αγ. Ιωάννης Ρέντης. Uvoznik za BiH: Pepco B-H d.o.o., ulica Skenderpašina br. 1, Opština Centar Sarajevo, 71 000 Sarajevo. klijent.ba@pepco.eu
Увозник/ Importuesi: ПЕПЦО ДООЕЛ Скопје, Ул. НАУМ НАУМОВСКИ - БОРЧЕ Бр.40/5-8 СКОПЈЕ - ЦЕНТАР ЦЕНТАР/ PEPCO DOOEL Shkup, Rruga Naum Naumovski-Borche Nr. 40/5-8, Shkup – Qendër, Maqedonia e Veriut. Імпортер: ТОВАРИСТВО З ОБМЕЖЕНОЮ ВІДПОВІДАЛЬНІСТЮ “ПЕПКО УКРАЇНА” вул. Загородня, 15,
м. Київ, 03150, Україна, customer@pepco.eu"""

    if combined_care:
        combined_care = f"{combined_care}\n\n\n\n\n\n\n\n\n\n{shrinkage_line}\n\n\n\n\n\n\n\n\n\n{bangladesh_line}"
    else:
        combined_care = f"{shrinkage_line}\n\n\n\n\n\n\n\n\n\n{bangladesh_line}"

    # ---------- Create DataFrame & Download ----------
    df = pd.DataFrame([{
        "washing_code": washing_code,
        "Composition_Care": combined_care
    }])

    final_cols = ["washing_code", "Composition_Care"]

    st.success("✅ Ready!")
    st.subheader("Preview")
    edited_df = st.data_editor(df[final_cols])

    csv_buffer = StringIO()
    writer = pycsv.writer(csv_buffer, delimiter=';', quoting=pycsv.QUOTE_ALL)
    writer.writerow(final_cols)
    for row in edited_df.itertuples(index=False):
        writer.writerow(row)

    custom_filename = f"PEPCO_CareLabel_{datetime.today().strftime('%Y%m%d_%H%M%S')}.csv"

    st.download_button(
        "📥 Download CSV",
        csv_buffer.getvalue().encode('utf-8-sig'),
        file_name=custom_filename,
        mime="text/csv"
    )


# ================================================================
#  MAIN APP
# ================================================================
def main():
    st.title("PEPCO Care Label Generator")
    
    if st.button("🆕 Reset"):
        for k in list(st.session_state.keys()):
            if k.startswith(("ui_", "mat_", "comp_", "care_", "composition_")):
                st.session_state.pop(k, None)
        st.rerun()
    
    process_pepco()
    
    st.markdown("---")
    st.caption("This app developed by Ovi")


if __name__ == "__main__":
    main()
