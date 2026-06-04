# -*- coding: utf-8 -*-
# main_exe/theme_engine.py
"""
ThemeEngine — نظام مركزي لتطبيق الثيم بدون إعادة تشغيل.

الاستخدام:
    from main_exe.theme_engine import ThemeEngine

    # في أي widget:
    ThemeEngine.subscribe(self._on_theme)

    def _on_theme(self, data: dict):
        self._btn.background_color = get_color_from_hex(data['accent'])
        ...

    # عند تغيير الثيم (يُستدعى من settings.py):
    ThemeEngine.apply('blue_sky')
"""

import weakref
from kivy.utils import get_color_from_hex


class _ThemeEngine:
    """Singleton يحتفظ بالثيم الحالي ويُخطر المشتركين عند التغيير."""

    def __init__(self):
        # قائمة weakref حتى لا تمنع garbage collection للـ widgets المحذوفة
        self._subscribers: list[weakref.ref] = []
        self._current_data: dict = {}

    # ──────────────────────────────────────────────────────────────────────────
    #  الاشتراك / إلغاء الاشتراك
    # ──────────────────────────────────────────────────────────────────────────

    def subscribe(self, callback):
        """
        يسجّل callback ليُستدعى عند كل تغيير في الثيم.
        callback يجب أن يقبل dict واحد: on_theme(data).
        إذا كان الثيم محدداً مسبقاً، يُستدعى callback فوراً.
        """
        ref = weakref.WeakMethod(callback) if hasattr(callback, '__self__') else weakref.ref(callback)
        self._subscribers.append(ref)
        # إذا كان الثيم محمّلاً بالفعل، أخبر المشترك الجديد فوراً
        if self._current_data:
            try:
                fn = ref()
                if fn:
                    fn(dict(self._current_data))
            except Exception:
                pass

    def unsubscribe(self, callback):
        """يُزيل callback من القائمة (اختياري — weakref تنظّف نفسها)."""
        self._subscribers = [
            r for r in self._subscribers
            if r() is not None and r() is not callback
        ]

    # ──────────────────────────────────────────────────────────────────────────
    #  تطبيق الثيم
    # ──────────────────────────────────────────────────────────────────────────

    def apply(self, theme_key: str, all_themes: dict):
        """
        يُطبّق الثيم على:
          1. THEME dict في main.py و main_exe/main.py (للتوافق مع الكود القديم)
          2. جميع المشتركين المسجّلين
        لا يُعيد تشغيل التطبيق.
        """
        if theme_key not in all_themes:
            theme_key = 'system'

        data = dict(all_themes[theme_key]['data'])
        self._current_data = data

        # ── تحديث THEME العالمي (للتوافق مع _c() في الملفات الأخرى) ──
        for module_name in ('main', 'main_exe.main'):
            try:
                import importlib
                mod = importlib.import_module(module_name)
                if hasattr(mod, 'THEME'):
                    mod.THEME.update(data)
            except Exception:
                pass

        # ── إخطار المشتركين ──────────────────────────────────────────
        self._notify(data)

    def _notify(self, data: dict):
        alive = []
        for ref in self._subscribers:
            fn = ref()
            if fn is None:
                continue          # widget محذوف — تجاهل
            alive.append(ref)
            try:
                fn(dict(data))    # نسخة مستقلة لكل مشترك
            except Exception as e:
                print(f'[ThemeEngine] subscriber error: {e}')
        self._subscribers = alive

    # ──────────────────────────────────────────────────────────────────────────
    #  دوال مساعدة للـ widgets
    # ──────────────────────────────────────────────────────────────────────────

    def color(self, key: str):
        """يُعيد لون من الثيم الحالي كـ RGBA tuple جاهز لـ Kivy."""
        hex_val = self._current_data.get(key, '#888888')
        return get_color_from_hex(hex_val)

    def hex(self, key: str) -> str:
        """يُعيد لون من الثيم الحالي كـ hex string."""
        return self._current_data.get(key, '#888888')

    @property
    def data(self) -> dict:
        """نسخة من بيانات الثيم الحالي (للقراءة فقط)."""
        return dict(self._current_data)


# Singleton وحيد للاستخدام في كل مكان
ThemeEngine = _ThemeEngine()