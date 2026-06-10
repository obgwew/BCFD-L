# -*- coding: utf-8 -*-
# main_exe/langs/translations.py

from .de import GERMAN_DICT
from .fr import FRENCH_DICT
from .ar import ARABIC_DICT
from .en import ENGLISH_DICT


class Translations:
    show_debug_ids = False

    translations = {
        'ar': ARABIC_DICT,
        'en': ENGLISH_DICT,
        'fr': FRENCH_DICT,
        'de': GERMAN_DICT,
    }

    @staticmethod
    def get(key: str, lang: str = 'en') -> str:
        val = Translations.translations.get(lang, {}).get(key, key)
        
        if isinstance(val, tuple) and len(val) == 2:
            num_id, text = val
            
            if Translations.show_debug_ids:
                return f"[{num_id}] {text}"
            
            return text
        
        return val

    @staticmethod
    def toggle_debug_ids():
        Translations.show_debug_ids = not Translations.show_debug_ids
