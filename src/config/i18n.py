import gettext

DEFAULT_LANGUAGE = "en"
SUPPORTED_LANGUAGES = ["en", "ru"]
DOMAIN = "base"
LOCALE_DIR = "locale"
_lang = DEFAULT_LANGUAGE


def activate_translation(lang: str):
    global _lang
    _lang = DEFAULT_LANGUAGE if lang not in SUPPORTED_LANGUAGES else lang


def _(message: str) -> str:
    if _lang == DEFAULT_LANGUAGE:
        return message
    return gettext.translation(DOMAIN, localedir=LOCALE_DIR, languages=[_lang]).gettext(
        message
    )
