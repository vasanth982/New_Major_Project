"""
i18n.py — Centralized Internationalization & Localization Engine for Checkup Buddy.
Supports 13 Pan-India Languages:
English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, Gujarati,
Punjabi, Odia, Assamese, and Urdu.
"""

import json
import os
import streamlit as st

LOCALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "locales")

SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "native": "English", "flag": "🌐"},
    "hi": {"name": "Hindi", "native": "हिन्दी", "flag": "🇮🇳"},
    "ta": {"name": "Tamil", "native": "தமிழ்", "flag": "🇮🇳"},
    "te": {"name": "Telugu", "native": "తెలుగు", "flag": "🇮🇳"},
    "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "flag": "🇮🇳"},
    "ml": {"name": "Malayalam", "native": "മലയാളം", "flag": "🇮🇳"},
    "bn": {"name": "Bengali", "native": "বাংলা", "flag": "🇮🇳"},
    "mr": {"name": "Marathi", "native": "मराठी", "flag": "🇮🇳"},
    "gu": {"name": "Gujarati", "native": "ગુજરાતી", "flag": "🇮🇳"},
    "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "flag": "🇮🇳"},
    "or": {"name": "Odia", "native": "ଓଡ଼ିଆ", "flag": "🇮🇳"},
    "as": {"name": "Assamese", "native": "অসমীয়া", "flag": "🇮🇳"},
    "ur": {"name": "Urdu", "native": "اردو", "flag": "🇮🇳"},
}

_TRANSLATIONS_CACHE = {}


_DEFAULT_LANGUAGE = "en"


def get_current_language() -> str:
    """Returns the currently active language code from session state, defaulting to 'en'."""
    try:
        if "language" not in st.session_state:
            st.session_state["language"] = _DEFAULT_LANGUAGE
        return st.session_state["language"]
    except Exception:
        return _DEFAULT_LANGUAGE


def set_language(lang_code: str):
    """Sets the active language code in session state."""
    global _DEFAULT_LANGUAGE
    if lang_code in SUPPORTED_LANGUAGES:
        _DEFAULT_LANGUAGE = lang_code
        try:
            st.session_state["language"] = lang_code
        except Exception:
            pass


def load_translations(lang_code: str) -> dict:
    """Loads translations dictionary for the given language code from locales/*.json."""
    if lang_code in _TRANSLATIONS_CACHE:
        return _TRANSLATIONS_CACHE[lang_code]

    file_path = os.path.join(LOCALES_DIR, f"{lang_code}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _TRANSLATIONS_CACHE[lang_code] = data
                return data
        except Exception as e:
            print(f"[i18n] Error loading {file_path}: {e}")

    # Fallback to English if file not found
    if lang_code != "en":
        return load_translations("en")
    return {}


def t(key: str, default: str = None, **kwargs) -> str:
    """
    Translates a key into the active language.
    Falls back to English if key is missing in target language.
    If still missing, returns `default` or the key itself.
    Supports str.format kwargs for dynamic interpolation.
    """
    current_lang = get_current_language()
    trans = load_translations(current_lang)
    val = trans.get(key)

    if val is None and current_lang != "en":
        en_trans = load_translations("en")
        val = en_trans.get(key)

    if val is None:
        val = default if default is not None else key

    if kwargs and isinstance(val, str):
        try:
            return val.format(**kwargs)
        except Exception:
            return val

    return val


def render_language_selector(key_suffix: str = "", label: str = None):
    """
    Renders an interactive language selector dropdown.
    Instantly updates st.session_state['language'] and triggers a rerun on change.
    """
    current_lang = get_current_language()
    options = list(SUPPORTED_LANGUAGES.keys())
    current_idx = options.index(current_lang) if current_lang in options else 0

    display_label = label if label is not None else t("language_label", default="🌐 Language / भाषा")

    def format_func(code):
        meta = SUPPORTED_LANGUAGES.get(code, {})
        return f"{meta.get('flag', '🌐')} {meta.get('native', code)} ({meta.get('name', code)})"

    selected_code = st.selectbox(
        display_label,
        options=options,
        index=current_idx,
        format_func=format_func,
        key=f"lang_selector_{key_suffix}"
    )

    if selected_code != current_lang:
        set_language(selected_code)
        st.rerun()
