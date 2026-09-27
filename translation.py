# ================================================================
#  translation.py
#  Multi-language product name (AL, ES, MK, etc) banano
#  app.py te use korte:
#      from translation import format_product_translations
# ================================================================
import pandas as pd

from composition_care import build_language_composition


# ================================================================
#  TRANSLATION FORMATTER (AL, ES, MK, etc)
#  composition_ctx: composition_care.render_composition_care_section()
#  er return-kora dict (components_data, materials_df,
#  comp_translations_df, use_advanced_mode) — AL/MK-er composition ei
#  ek-i data theke ashe, Composition_Care column-er shathe same thake.
# ================================================================
def format_product_translations(
    product_name,
    translation_row,
    composition_ctx=None,
):
    """Builds multilingual product description with material info."""
    formatted = []

    # Country suffix rules
    country_suffixes = {
        'BiH': " Sastav materijala na ušivenoj etiketi.",
        'RS': " Sastav materijala nalazi se na ušivenoj etiketi.",
        'UA': " Імпортер приймає претензії. Термін придатності – необмежений, якщо продукт використовується за призначенням (якщо на упаковці або продукті не вказано термін придатності). Умови зберігання – Зберігати в сухому місці при кімнатній температурі.",
    }

    # EN fallback
    en_text = translation_row.get('EN', product_name)
    formatted.append(f"|EN| {en_text}")

    # ES / ES_CA combined
    combined_lang = {
        'ES': (
            f"{translation_row['ES']} / {translation_row['ES_CA']}"
            if pd.notna(translation_row.get('ES_CA'))
            else translation_row.get('ES')
        )
    }

    # Language order defined
    language_order = [
        'AL', 'BG', 'BiH', 'CZ', 'DE', 'EE',
        'ES', 'GR', 'HR', 'HU', 'IT', 'LT',
        'LV', 'MK', 'PL', 'PT', 'RO', 'RS',
        'SI', 'SK', 'UA'
    ]

    components_data = composition_ctx["components_data"] if composition_ctx else []

    # Build translations
    for lang in language_order:
        if lang in combined_lang and combined_lang[lang] is not None:
            text = combined_lang[lang]
        else:
            text = translation_row.get(lang, product_name)

        # Composition for AL + MK only — composition_care.py-r data theke
        if components_data and lang in ['AL', 'MK']:
            comp_text = build_language_composition(
                components_data,
                composition_ctx["materials_df"],
                composition_ctx["comp_translations_df"],
                lang,
                composition_ctx["use_advanced_mode"],
            )
            if comp_text:
                text = f"{text}: {comp_text}"

        # Country suffix
        if lang in country_suffixes:
            if not text.endswith('.'):
                text += "."
            text += country_suffixes[lang]

        formatted.append(f"|{lang}| {text}")

    return " ".join(formatted)
