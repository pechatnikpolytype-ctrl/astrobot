"""Мультиязычность: загрузка переводов."""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Кэш загруженных языков
_LOADED = {}

SUPPORTED = ["ru", "en", "de"]
DEFAULT = "ru"


def _load(lang: str) -> dict:
    if lang in _LOADED:
        return _LOADED[lang]
    try:
        if lang == "ru":
            from . import ru as mod
        elif lang == "en":
            from . import en as mod
        elif lang == "de":
            from . import de as mod
        else:
            from . import ru as mod
        data = {k: v for k, v in vars(mod).items() if not k.startswith("_") and isinstance(v, (str, dict, list))}
        _LOADED[lang] = data
        return data
    except Exception as e:
        logger.error(f"Ошибка загрузки locale {lang}: {e}")
        return {}


def t(key: str, lang: str = DEFAULT, **kwargs) -> str:
    """
    Возвращает перевод по ключу.
    Если ключа нет — вернёт сам ключ (чтобы видеть что пропущено).
    kwargs — подстановки в шаблоне.
    """
    if lang not in SUPPORTED:
        lang = DEFAULT
    data = _load(lang)
    text = data.get(key)
    if text is None:
        # fallback на русский
        data = _load(DEFAULT)
        text = data.get(key, key)
    if not isinstance(text, str):
        return str(text)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def t_dict(key: str, lang: str = DEFAULT) -> dict:
    """Возвращает словарь (для меню-кнопок)."""
    if lang not in SUPPORTED:
        lang = DEFAULT
    data = _load(lang)
    val = data.get(key)
    if not isinstance(val, dict):
        data = _load(DEFAULT)
        val = data.get(key, {})
    return val if isinstance(val, dict) else {}


def get_lang_name(code: str) -> str:
    """Человекочитаемое имя языка."""
    return {
        "ru": "🇷🇺 Русский",
        "en": "🇬🇧 English",
        "de": "🇩🇪 Deutsch",
    }.get(code, code)


def detect_from_telegram(tg_code: str) -> str:
    """Определяет язык из telegram.language_code."""
    if not tg_code:
        return DEFAULT
    code = tg_code.lower().split("-")[0]
    if code in SUPPORTED:
        return code
    return DEFAULT
