import json
import os
from typing import Dict

LOCALES_PATH = os.path.join(os.path.dirname(__file__), '../locales')

_cache: Dict[str, Dict[str, str]] = {}

def load_translations(lang: str) -> Dict[str, str]:
    if lang in _cache:
        return _cache[lang]
    try:
        with open(os.path.join(LOCALES_PATH, f'{lang}.json'), encoding='utf-8') as f:
            data = json.load(f)
            _cache[lang] = data
            return data
    except Exception:
        return {}

def translate(key: str, lang: str = 'ru') -> str:
    translations = load_translations(lang)
    return translations.get(key) or key 