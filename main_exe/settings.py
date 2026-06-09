# Copyright (C) 2026 obgwew
# SPDX-License-Identifier: AGPL-3.0-or-later

# -*- coding: utf-8 -*-
# main_exe/settings.py . migrated to Flet 0.80+ / v1 API

import os
import sys
import json
import zipfile
import webbrowser
import random
import shutil
import subprocess

import flet as ft
import arabic_reshaper
from bidi.algorithm import get_display

from main_exe.langs.translations import Translations
from main_exe.theme_engine import ThemeEngine

# ══════════════════════════════════════════════════════════════════════════════
#  Settings file path
# ══════════════════════════════════════════════════════════════════════════════

_SETTINGS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app_data/settings.json')
)

# ══════════════════════════════════════════════════════════════════════════════
#  Read / Write settings
# ══════════════════════════════════════════════════════════════════════════════

def load_settings() -> dict:
    try:
        with open(_SETTINGS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(patch: dict):
    data = load_settings()
    data.update(patch)
    try:
        with open(_SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f'[Settings] save failed: {e}')


def get_current_theme() -> str:
    return load_settings().get('theme', 'system_wh')


def get_current_lang() -> str:
    return load_settings().get('lang', 'en')


def _pending_beta_flags(d: dict = None) -> int:
    if d is None:
        d = load_settings()
    _base  = len([k for k in d if not k.startswith('_')])
    _score = d.get('_ul', 0)
    return _base + _score


def _ui_profile_fixed() -> bool:
    return _pending_beta_flags() > 10


# ══════════════════════════════════════════════════════════════════════════════
#  Translation helper
# ══════════════════════════════════════════════════════════════════════════════

_FALLBACKS = {
    'general_section':   'General',
    'language':          'Language',
    'save':              'Save',
    'design_section':    'Appearance',
    'info_section':      'Information',
    'wiki':              'Wiki',
    'github':            'GitHub',
    'discord':           'Discord',
    'link':              '↗ Open link',
    'bot_name_hint':     'Bot Name',
    'bot_token_hint':    'Bot Token',
    'token_required':    'Token is required',
    'theme_system':      'System (Default)',
    'theme_blue_sky':    'Blue Sky',
    'theme_yellow_bile': 'Yellow',
    'theme_win7':        'Win7',
    'theme_v2_dark':     'Dark Gold',
    'export_section':    'Export Bot Data',
    'export_desc':       'Export commands and variables as a ZIP file',
    'export_zip':        'Export ZIP',
    'no_bot_selected':   'No bot selected!',
    'folders_not_found': 'Folders not found!',
    'export_failed':     'Export failed!',
    'danger_zone':       'Danger Zone',
    'delete_bot_perm':   'Delete This Bot Permanently',
    'captcha_enter':     'Enter 3 digits',
    'captcha_hint':      'Enter the 3 digits shown above',
    'confirm_delete':    'Confirm Delete',
    'captcha_wrong':     'Incorrect code — try again',
}

def reshape_arabic(text: str) -> str:
    if not isinstance(text, str):
        return text
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    return bidi_text

def _t(key: str) -> str:
    val = Translations.get(key, get_current_lang())
    return val if val else _FALLBACKS.get(key, key)

def _ar(text: str) -> str:
    if get_current_lang() in ['ar', 'arabic', 'AR']:
        return reshape_arabic(text)
    return text


# ══════════════════════════════════════════════════════════════════════════════
#  Theme color shortcut
# ══════════════════════════════════════════════════════════════════════════════

def _c(key: str) -> str:
    return ThemeEngine.hex(key)


# ══════════════════════════════════════════════════════════════════════════════
#  Themes
# ══════════════════════════════════════════════════════════════════════════════

ALL_THEMES = {
    'system_wh': {
        'swatch_a': '#1B1F2E',
        'swatch_b': '#ECF1FF',
        'data': {
            'bg':             '#FFFFFF',
            'card_bg':        '#E3E9FA',
            'card_border':    '#FFFFFF',
            'footer_bg':      '#D6E7FD',
            'popup_bg':       '#FFFFFF',
            'input_bg':       '#4E4E4E',
            'input_border':   '#5A5A5A',
            'text':           '#000000',
            'text_dim':       '#5C5C5C',
            'text_on_accent': '#FFFFFF',
            'accent':         '#1B1F2E',
            'accent_hover':   '#2C3150',
            'success':        '#16A34A',
            'danger':         '#DC2626',
            'icon_bg':        '#8F8F8F',
            'discord':        '#5865F2',
            'github':         '#24292E',
            'title_bcfd':     '#1B1F2E',
            'nav_bg':         '#E8EDFF',
            'nav_active':     '#000000',
            'nav_inactive':   '#555555',
            'divider':        '#E4E8F0',
            'online':         '#16A34A',
            'offline':        '#DC2626',
            'btn_invite':     '#5865F2',
        },
    },
    'blue_sky': {
        'swatch_a': '#0D47A1',
        'swatch_b': '#BBDEFB',
        'data': {
            'bg':             '#E8F6FF',
            'card_bg':        '#BBDEFB',
            'card_border':    '#90CAF9',
            'footer_bg':      '#90CAF9',
            'popup_bg':       '#E8F6FF',
            'input_bg':       '#64B5F6',
            'input_border':   '#42A5F5',
            'text':           '#0D47A1',
            'text_dim':       '#1565C0',
            'text_on_accent': '#FFFFFF',
            'accent':         '#0D47A1',
            'accent_hover':   '#1565C0',
            'success':        '#2E7D32',
            'danger':         '#C62828',
            'icon_bg':        '#64B5F6',
            'discord':        '#5865F2',
            'github':         '#0D47A1',
            'title_bcfd':     '#0D47A1',
            'nav_bg':         '#1565C0',
            'nav_active':     '#FFFFFF',
            'nav_inactive':   '#90CAF9',
            'divider':        '#90CAF9',
            'online':         '#2E7D32',
            'offline':        '#C62828',
            'btn_invite':     '#5865F2',
        },
    },
    'yellow_bile': {
        'swatch_a': '#FFFB00',
        'swatch_b': '#FFF7AD',
        'data': {
            'bg':             '#FFFDE7',
            'card_bg':        '#FFF9C4',
            'card_border':    '#FFE70C',
            'footer_bg':      '#FFEE58',
            'popup_bg':       '#FFFDE7',
            'input_bg':       '#FFFB28',
            'input_border':   '#FFB300',
            'text':           '#3E2723',
            'text_dim':       '#5D4037',
            'text_on_accent': '#FFFFFF',
            'accent':         '#E65100',
            'accent_hover':   '#BF360C',
            'success':        '#2E7D32',
            'danger':         '#B71C1C',
            'icon_bg':        '#FFCA28',
            'discord':        '#5865F2',
            'github':         '#3E2723',
            'title_bcfd':     '#E65100',
            'nav_bg':         '#F57F17',
            'nav_active':     '#FFFFFF',
            'nav_inactive':   '#FFF9C4',
            'divider':        '#F9A825',
            'online':         '#2E7D32',
            'offline':        '#B71C1C',
            'btn_invite':     '#5865F2',
        },
    },
    'system_da': {
        'swatch_a': "#6D6D6D",
        'swatch_b': "#1A1A1A",
        'data': {
            ' bg':             '#1A1C26',
            'card_bg':        '#23263A',
            'card_border':    '#2E3250',
            'footer_bg':      '#1E2133',
            'popup_bg':       '#23263A',
            'input_bg':       '#2A2D40',
            'input_border':   '#3A3F5C',
            'text':           '#E8EAF6',
            'text_dim':       '#7B82A8',
            'text_on_accent': '#FFFFFF',
            'accent':         '#4A90D9',
            'accent_hover':   '#5BA3EC',
            'success':        '#2E7D32',
            'danger':         '#CF6679',
            'icon_bg':        '#2E3250',
            'discord':        '#5865F2',
            'github':         '#E8EAF6',
            'title_bcfd':     '#E8EAF6',
            'nav_bg':         '#1E2133',
            'nav_active':     '#FFFFFF',
            'nav_inactive':   '#7B82A8',
            'divider':        '#2E3250',
            'online':         '#2E7D32',
            'offline':        '#CF6679',
            'btn_invite':     '#5865F2',
        },
    },
    'v2_dark': {
        'swatch_a': '#0D1B2A',
        'swatch_b': '#C9A227',
        'data': {
            'bg':             '#0D1B2A',
            'card_bg':        '#12243A',
            'card_border':    '#C9A227',
            'footer_bg':      '#090F18',
            'popup_bg':       '#12243A',
            'input_bg':       '#1A2F4A',
            'input_border':   '#C9A227',
            'text':           '#E8DEB0',
            'text_dim':       '#8A7D50',
            'text_on_accent': '#0D1B2A',
            'accent':         '#C9A227',
            'accent_hover':   '#D4B040',
            'success':        '#2A8050',
            'danger':         '#A03030',
            'icon_bg':        '#1A2F4A',
            'discord':        '#5865F2',
            'github':         '#E8DEB0',
            'title_bcfd':     '#C9A227',
            'nav_bg':         '#090F18',
            'nav_active':     '#C9A227',
            'nav_inactive':   '#8A7D50',
            'divider':        '#2A3F5A',
            'online':         '#2A8050',
            'offline':        '#A03030',
            'btn_invite':     '#5865F2',
        },
    },
}

_All_THEMES = ['system_wh','system_da', 'blue_sky', 'yellow_bile']
_PKEY       = ''.join(k[0] for k in _All_THEMES)
_PLT_REF    = next((k for k in ALL_THEMES if k not in _All_THEMES), None)

# ══════════════════════════════════════════════════════════════════════════════
#  Theme integration
# ══════════════════════════════════════════════════════════════════════════════

def apply_theme_globally(theme_key: str):
    ThemeEngine.apply(theme_key, ALL_THEMES)

    d     = load_settings()
    patch = {'theme': theme_key}

    _prev  = d.get('theme', '')
    _depth = d.get('_ul', 0)
    _warm  = {'blue_sky', 'yellow_bile'}

    if _prev in _warm and theme_key in _warm and _prev != theme_key:
        _depth += 2
    elif theme_key in _warm:
        _depth += 1
    else:
        _depth = max(0, _depth - 1)

    patch['_ul'] = _depth
    save_settings(patch)


# ══════════════════════════════════════════════════════════════════════════════
#  Card helper
# ══════════════════════════════════════════════════════════════════════════════

def _border_all(w: float, color: str) -> ft.Border:
    s = ft.BorderSide(w, color)
    return ft.Border(left=s, top=s, right=s, bottom=s)

def _card_container(content: ft.Control) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=_c('card_bg'),
        border=_border_all(1, _c('card_border')),
        border_radius=14,
        padding=ft.Padding(left=16, top=14, right=16, bottom=14),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  BotSettingsTab
# ══════════════════════════════════════════════════════════════════════════════

class BotSettingsTab:

    def __init__(self, page: ft.Page, bot_data: dict = None,
                 on_bot_save=None, on_theme_change=None):
        self._page            = page
        self._bot_data        = bot_data or {}
        self._on_bot_save     = on_bot_save
        self._on_theme_change = on_theme_change

        self._lang          = get_current_lang()
        self._current_theme = get_current_theme()
        self._theme_btns: dict[str, ft.FilledButton] = {}
        self._ext_ui_active = _ui_profile_fixed()

        self._export_status_text = ft.Text('', size=11, color=_c('success'))

        self._captcha_code    = ''
        self._captcha_display = ft.Text(
            '', size=26, weight=ft.FontWeight.BOLD,
            color=_c('text'), selectable=False,
        )
        self._captcha_field = ft.TextField(
            hint_text=_t('captcha_enter'),
            dense=True, max_length=3,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color=_c('card_border'),
            focused_border_color=_c('danger'),
            cursor_color=_c('danger'),
            text_style=ft.TextStyle(color=_c('text'), size=13),
        )
        self._captcha_section = ft.Column([], spacing=8, visible=False)

        self._delete_init_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.DELETE_FOREVER, color='#FFFFFF'),
                 ft.Text(_t('delete_bot_perm'), color='#FFFFFF',
                         weight=ft.FontWeight.BOLD)],
                spacing=6, tight=True,
            ),
            on_click=self._show_captcha,
            style=ft.ButtonStyle(bgcolor=_c('danger'), color='#FFFFFF'),
        )

        self._name_field = ft.TextField(
            label=_t('bot_name_hint'),
            dense=True,
            border_color=_c('card_border'),
            focused_border_color=_c('accent'),
            cursor_color=_c('accent'),
            label_style=ft.TextStyle(color=_c('text_dim'), size=12),
            text_style=ft.TextStyle(color=_c('text'), size=13),
            bgcolor=_c('card_bg'),
        )
        self._token_field = ft.TextField(
            label=_t('bot_token_hint'),
            dense=True,
            password=True,
            can_reveal_password=True,
            border_color=_c('card_border'),
            focused_border_color=_c('accent'),
            cursor_color=_c('accent'),
            label_style=ft.TextStyle(color=_c('text_dim'), size=12),
            text_style=ft.TextStyle(color=_c('text'), size=13),
            bgcolor=_c('card_bg'),
        )

        self._design_col = ft.Column(spacing=4)
        self._btn_en: ft.FilledButton = None
        self._btn_ar: ft.FilledButton = None

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        return ft.Column(
            [
                ft.Column(
                    [
                        self._build_general_section(),
                        self._build_export_section(),
                        self._build_design_section(),
                        self._build_info_section(),
                        self._build_delete_section(),
                        ft.Container(height=16),
                    ],
                    spacing=20,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                ),
            ],
            expand=True,
        )

    # ── Section: General ──────────────────────────────────────────────────────

    def _build_general_section(self) -> ft.Control:
        self._btn_en = self._lang_btn('EN', 'en')
        self._btn_ar = self._lang_btn('AR', 'ar')
        self._refresh_lang_btns()

        return ft.Column(
            [
                self._section_title(_t('general_section')),
                _card_container(
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(_t('language'), size=13,
                                            color=_c('text'), expand=True,
                                            weight=ft.FontWeight.W_500),
                                    self._btn_en,
                                    self._btn_ar,
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Divider(color=_c('divider'), height=1),
                            self._name_field,
                            self._token_field,
                            ft.FilledButton(
                                content=ft.Row(
                                    [ft.Icon(ft.Icons.SAVE_OUTLINED, color='#FFFFFF', size=16),
                                     ft.Text(_t('save'), color='#FFFFFF',
                                             weight=ft.FontWeight.BOLD)],
                                    spacing=6, tight=True,
                                ),
                                on_click=self._save_bot,
                                style=ft.ButtonStyle(
                                    bgcolor=_c('success'),
                                    color='#FFFFFF',
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                    padding=ft.Padding(left=14, top=10, right=14, bottom=10),
                                ),
                            ),
                        ],
                        spacing=12,
                    ),
                ),
            ],
            spacing=8,
        )

    # ── Section: Export ───────────────────────────────────────────────────────

    def _build_export_section(self) -> ft.Control:
        return ft.Column(
            [
                self._section_title(_t('export_section')),
                _card_container(
                    ft.Column(
                        [
                            ft.Text(
                                _t('export_desc'),
                                size=12, color=_c('text_dim'),
                            ),
                            ft.Divider(color=_c('divider'), height=1),
                            ft.Row(
                                [
                                    ft.FilledButton(
                                        content=ft.Row(
                                            [ft.Icon(ft.Icons.ARCHIVE_OUTLINED, color='#FFFFFF', size=16),
                                             ft.Text(_t('export_zip'),
                                                     color='#FFFFFF', weight=ft.FontWeight.BOLD)],
                                            spacing=6, tight=True,
                                        ),
                                        on_click=self._export_bot_data,
                                        style=ft.ButtonStyle(bgcolor=_c('accent'), color='#FFFFFF', shape=ft.RoundedRectangleBorder(radius=10)),
                                    ),
                                    self._export_status_text,
                                ],
                                spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=10,
                    ),
                ),
            ],
            spacing=8,
        )

    # ── Section: Design / Themes ──────────────────────────────────────────────

    def _build_design_section(self) -> ft.Control:
        visible = list(_All_THEMES)
        if self._ext_ui_active and _PLT_REF:
            visible.append(_PLT_REF)

        self._design_col.controls.clear()
        for key in visible:
            self._design_col.controls.append(self._theme_row(key))

        return ft.Column(
            [
                self._section_title(_t('design_section')),
                _card_container(self._design_col),
            ],
            spacing=8,
        )

    # ── Section: Information ──────────────────────────────────────────────────

    def _build_info_section(self) -> ft.Control:
        rows = [
            ('wiki',    'https://github.com/obgwew/BCFD-L/blob/main/wiki.md'),
            ('github',  'https://github.com/obgwew/BCFD-L'),
            ('discord', 'https://discord.gg/JngaJRC6Y9'),
        ]
        return ft.Column(
            [
                self._section_title(_t('info_section')),
                _card_container(
                    ft.Column(
                        [self._info_row(lk, url) for lk, url in rows],
                        spacing=8,
                    ),
                ),
            ],
            spacing=8,
        )

    # ── Section: Delete (Danger Zone) ─────────────────────────────────────────

    def _build_delete_section(self) -> ft.Control:
        self._captcha_section = ft.Column(
            [
                ft.Container(
                    content=ft.Column([self._captcha_display], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=_c('card_bg'),
                    border=_border_all(2, _c('danger')),
                    border_radius=8,
                    padding=ft.Padding(left=10, top=10, right=10, bottom=10),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Text(_t('captcha_hint'), size=12, color=_c('text_dim')),
                self._captcha_field,
                ft.FilledButton(
                    content=ft.Row(
                        [ft.Icon(ft.Icons.WARNING_ROUNDED, color='#FFFFFF'),
                         ft.Text(_t('confirm_delete'), color='#FFFFFF', weight=ft.FontWeight.BOLD)],
                        spacing=6, tight=True,
                    ),
                    on_click=self._execute_deletion,
                    expand=True,
                    style=ft.ButtonStyle(bgcolor='#991B1B', color='#FFFFFF', shape=ft.RoundedRectangleBorder(radius=10)),
                ),
            ],
            spacing=10,
            visible=False,
        )

        return ft.Column(
            [
                ft.Text(_t('danger_zone'), size=13, weight=ft.FontWeight.BOLD, color=_c('danger')),
                _card_container(
                    ft.Column([self._delete_init_btn, self._captcha_section], spacing=10),
                ),
            ],
            spacing=8,
        )

    # ── UI element builders ───────────────────────────────────────────────────

    def _section_title(self, text: str) -> ft.Text:
        return ft.Text(
            text, size=12,
            weight=ft.FontWeight.BOLD,
            color=_c('text_dim'),
        )

    def _lang_btn(self, label: str, code: str) -> ft.FilledButton:
        return ft.FilledButton(
            content=ft.Text(label, weight=ft.FontWeight.BOLD),
            on_click=lambda _, c=code: self._set_lang(c),
            style=ft.ButtonStyle(
                bgcolor=_c('card_bg'),
                color=_c('text'),
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=14, top=6, right=14, bottom=6),
            ),
        )

    def _theme_row(self, theme_key: str) -> ft.Control:
        info   = ALL_THEMES[theme_key]
        is_sel = theme_key == self._current_theme

        swatches = [info['swatch_a'], info['swatch_b']]
        if 'swatch_c' in info:
            swatches.extend([info['swatch_c'], info.get('swatch_d', info['swatch_b'])])

        swatch_widgets = [
            ft.Container(
                width=18, height=34,
                bgcolor=col,
                border_radius=ft.BorderRadius(
                    top_left=8    if i == 0                  else 0,
                    bottom_left=8 if i == 0                  else 0,
                    top_right=8   if i == len(swatches) - 1 else 0,
                    bottom_right=8 if i == len(swatches) - 1 else 0,
                ),
            )
            for i, col in enumerate(swatches)
        ]

        swatch = ft.Container(
            content=ft.Row(swatch_widgets, spacing=0),
            border=_border_all(1, _c('card_border')),
            border_radius=8,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            width=18 * len(swatches),
            height=34,
        )

        sel_btn = ft.FilledButton(
            content=ft.Text(
                '✓' if is_sel else '>',
                color='#FFFFFF' if is_sel else _c('text_dim'),
                weight=ft.FontWeight.BOLD,
            ),
            on_click=lambda _, k=theme_key: self._select_theme(k),
            style=ft.ButtonStyle(
                bgcolor=_c('accent') if is_sel else _c('card_border'),
                color='#FFFFFF',
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=12, top=4, right=12, bottom=4),
            ),
        )
        self._theme_btns[theme_key] = sel_btn

        return ft.Container(
            content=ft.Row(
                [
                    swatch,
                    ft.Text(
                        _t('theme_' + theme_key),
                        size=13,
                        color=_c('text'),
                        weight=ft.FontWeight.W_500,
                        expand=True,
                    ),
                    sel_btn,
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=52,
            border_radius=10,
            bgcolor=_c('accent') + '18' if is_sel else 'transparent',
            padding=ft.Padding(left=6, right=6, top=0, bottom=0),
        )

    def _info_row(self, label_key: str, url: str) -> ft.Control:
        icons = {'wiki': ft.Icons.MENU_BOOK_OUTLINED,
                 'github': ft.Icons.CODE,
                 'discord': ft.Icons.TAG}
        colors = {'wiki': _c('accent'),
                  'github': _c('accent'),
                  'discord': '#5865F2'}

        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(icons.get(label_key, ft.Icons.LINK),
                            color=colors.get(label_key, _c('accent')), size=18),
                    ft.Text(_t(label_key), size=13, color=_c('text'),
                            weight=ft.FontWeight.W_500, expand=True),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW_ROUNDED,
                        icon_color=_c('text_dim'),
                        icon_size=16,
                        on_click=lambda _, u=url: webbrowser.open(u),
                        style=ft.ButtonStyle(shape=ft.CircleBorder()),
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            height=44,
            border_radius=8,
            padding=ft.Padding(left=4, right=0, top=0, bottom=0),
        )

    # ── Language ──────────────────────────────────────────────────────────────

    def _set_lang(self, code: str):
        self._lang = code
        save_settings({'lang': code})
        self._refresh_lang_btns()
        self._page.update()

    def _refresh_lang_btns(self):
        if not self._btn_en or not self._btn_ar:
            return
        for btn, code in [(self._btn_en, 'en'), (self._btn_ar, 'ar')]:
            active = code == self._lang
            btn.style = ft.ButtonStyle(
                bgcolor=_c('accent') if active else _c('card_bg'),
                color='#FFFFFF' if active else _c('text'),
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=14, top=6, right=14, bottom=6),
            )

    # ── Theme selection ───────────────────────────────────────────────────────

    def _select_theme(self, theme_key: str):
        apply_theme_globally(theme_key)
        self._current_theme = theme_key

        if _ui_profile_fixed() and not self._ext_ui_active:
            self._ext_ui_active = True
            if _PLT_REF:
                self._design_col.controls.append(self._theme_row(_PLT_REF))

        for key, btn in self._theme_btns.items():
            active = key == theme_key
            btn.content = ft.Text(
                '✓' if active else '>',
                color='#FFFFFF' if active else _c('text_dim'),
                weight=ft.FontWeight.BOLD,
            )
            btn.style = ft.ButtonStyle(
                bgcolor=_c('accent') if active else _c('card_border'),
                color='#FFFFFF',
                shape=ft.RoundedRectangleBorder(radius=8),
                padding=ft.Padding(left=12, top=4, right=12, bottom=4),
            )

        if self._on_theme_change:
            self._on_theme_change(theme_key)

        self._page.update()

    # ── Export ────────────────────────────────────────────────────────────────

    def _export_bot_data(self, _):
        bot_name = self._bot_data.get('name', '').strip()
        bot_dir  = self._bot_data.get('bot_dir', '').strip()

        if not bot_name or not bot_dir:
            self._export_status_text.color = _c('danger')
            self._export_status_text.value = _t('no_bot_selected')
            self._page.update()
            return

        base_dir   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        export_dir = os.path.normpath(os.path.join(base_dir, 'app_data', 'exports'))
        os.makedirs(export_dir, exist_ok=True)

        zip_name = f'{bot_name}_export.zip'
        zip_path = os.path.join(export_dir, zip_name)

        sources = {}
        for folder in ['bot_commands', 'bot_vars']:
            candidate = os.path.normpath(
                os.path.join(base_dir, 'app_data', bot_name, folder)
            )
            if not os.path.isdir(candidate):
                candidate = os.path.normpath(os.path.join(bot_dir, folder))
            if os.path.isdir(candidate):
                sources[folder] = candidate

        if not sources:
            self._export_status_text.color = _c('danger')
            self._export_status_text.value = _t('folders_not_found')
            self._page.update()
            return

        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for folder_name, folder_path in sources.items():
                    for root, _, files in os.walk(folder_path):
                        for file in files:
                            abs_p = os.path.join(root, file)
                            arc   = os.path.join(
                                folder_name, os.path.relpath(abs_p, folder_path)
                            )
                            zf.write(abs_p, arc)

            try:
                if sys.platform == 'win32':
                    subprocess.Popen(['explorer', '/select,', zip_path])
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', '-R', zip_path])
                else:
                    subprocess.Popen(['xdg-open', export_dir])
            except Exception:
                pass

            self._export_status_text.color = _c('success')
            self._export_status_text.value = _ar(f'✓ exports/{zip_name}')

        except Exception as e:
            print(f'[Settings] Export failed: {e}')
            self._export_status_text.color = _c('danger')
            self._export_status_text.value = _t('export_failed')

        self._page.update()

    # ── Delete / Captcha ──────────────────────────────────────────────────────

    def _show_captcha(self, _):
        self._captcha_code             = ''.join(random.choices('0123456789', k=3))
        self._captcha_display.value    = self._captcha_code
        self._captcha_field.value      = ''
        self._captcha_field.error_text = None
        self._captcha_section.visible  = True
        self._delete_init_btn.visible  = False
        self._page.update()

    def _execute_deletion(self, _):
        if (self._captcha_field.value or '').strip() != self._captcha_code:
            self._captcha_code          = ''.join(random.choices('0123456789', k=3))
            self._captcha_display.value = self._captcha_code
            self._captcha_field.value   = ''
            self._captcha_field.error_text = _t('captcha_wrong')
            self._page.update()
            return

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bot_name = self._bot_data.get('name', '')

        if bot_name:
            target = os.path.normpath(os.path.join(base_dir, 'app_data', bot_name))
            if os.path.exists(target):
                try:
                    shutil.rmtree(target)
                    print(f'[Settings] Deleted: {target}')
                except Exception as e:
                    print(f'[Settings] Delete failed: {e}')

        if self._on_bot_save:
            self._on_bot_save({})

        bcfd_path = os.path.normpath(os.path.join(base_dir, 'BCFD.py'))
        try:
            subprocess.Popen([sys.executable, bcfd_path])
        except Exception as e:
            print(f'[Settings] Relaunch failed: {e}')

        sys.exit(0)

    # ── Save Bot ──────────────────────────────────────────────────────────────

    def _save_bot(self, _):
        new_name  = (self._name_field.value or '').strip()
        new_token = (self._token_field.value or '').strip()

        if not new_token:
            self._token_field.error_text = _t('token_required')
            self._page.update()
            return

        self._token_field.error_text = None
        bot_dir = self._bot_data.get('bot_dir', '')

        if bot_dir:
            config_path = os.path.join(bot_dir, 'bot_files', 'config.json')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    cfg = json.load(f)
                cfg['name']  = new_name or cfg.get('name', 'Bot')
                cfg['token'] = new_token
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                self._bot_data.update({'name': cfg['name'], 'token': new_token})
            except Exception as e:
                print(f'[Settings] save failed: {e}')

        if self._on_bot_save:
            self._on_bot_save(self._bot_data)

        self._page.update()

    # ── Load Bot ──────────────────────────────────────────────────────────────

    def load_bot(self, bot_data: dict):
        self._bot_data          = bot_data
        self._name_field.value  = bot_data.get('name',  '')
        self._token_field.value = bot_data.get('token', '')