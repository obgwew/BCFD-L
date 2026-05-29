# -*- coding: utf-8 -*-
# main_exe/settings.py

import os
import json
import webbrowser

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse

from main_exe.langs.translations import Translations
from main_exe.theme_engine import ThemeEngine

# ══════════════════════════════════════════════════════════════════════════════
#  مسار ملف الاعدادات
# ══════════════════════════════════════════════════════════════════════════════

_SETTINGS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'app_data/settings.json')
)

# ══════════════════════════════════════════════════════════════════════════════
#  قراءة / كتابة الاعدادات
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
        print(f"[Settings] save failed: {e}")


def get_current_theme() -> str:
    return load_settings().get('theme', 'system')


def get_current_lang() -> str:
    return load_settings().get('lang', 'en')


def _pending_beta_flags(d: dict = None) -> int:
    if d is None:
        d = load_settings()
    _base  = len([k for k in d if not k.startswith('_')])
    _score = d.get('_ul', 0)
    return _base + _score


def _ui_profile_fixed() -> bool:
    # اداة التصحيح التلقائي اذا تغيرت الثيم بسرعة اكثر من 10 مرات
    return _pending_beta_flags() > 10


# ══════════════════════════════════════════════════════════════════════════════
#  TRANSLATION HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _t(key: str) -> str:
    return Translations.get(key, get_current_lang())


# ══════════════════════════════════════════════════════════════════════════════
#  THEMES
# ══════════════════════════════════════════════════════════════════════════════

ALL_THEMES = {

    'system': {
        'swatch_a': '#1B1F2E',
        'swatch_b': "#ECF1FF",
        'data': {
            'bg':             '#FFFFFF',
            'card_bg':        "#E3E9FA",
            'card_border':    '#FFFFFF',
            'footer_bg':      "#D6E7FD",
            'popup_bg':       '#FFFFFF',
            'input_bg':       "#4E4E4E",
            'input_border':   "#5A5A5A",
            'text':           '#000000',
            'text_dim':       "#5C5C5C",
            'text_on_accent': "#838383",
            'accent':         '#1B1F2E',
            'accent_hover':   '#2C3150',
            'success':        '#16A34A',
            'danger':         '#DC2626',
            'icon_bg':        '#8F8F8F',
            'discord':        '#5865F2',
            'github':         '#24292E',
            'title_bcfd':     '#1B1F2E',
            'nav_bg':         "#E8EDFF",
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
        'swatch_a': "#FFFB00",
        'swatch_b': "#FFF7AD",
        'data': {
            'bg':             '#FFFDE7',
            'card_bg':        '#FFF9C4',
            'card_border':    "#FFE70C",
            'footer_bg':      '#FFEE58',
            'popup_bg':       '#FFFDE7',
            'input_bg':       "#FFFB28",
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

    'win7': {
        'swatch_a': "#1EFF00",
        'swatch_b': "#EEFF00",
        'swatch_c': '#0078D7',
        'swatch_d': "#FF0000",
        'data': {
            'bg':             "#FFFFFF",
            'card_bg':        "#3700FF",
            'card_border':    "#00027C",
            'footer_bg':      "#EEFF00",
            'popup_bg':       "#B90000",
            'input_bg':       "#C90000",
            'input_border':   "#FBFF00",
            'text':           '#E0F0FF',
            'text_dim':       '#8AAFCF',
            'text_on_accent': "#B30000",
            'accent':         "#1EB300",
            'accent_hover':   "#0068B8",
            'success':        '#4CAF50',
            'danger':         '#F44336',
            'icon_bg':        '#4A7DB5',
            'discord':        "#7972DA",
            'github':         "#001529",
            'title_bcfd':     "#00C410",
            'nav_bg':         "#00027A",
            'nav_active':     '#FFFFFF',
            'nav_inactive':   '#90CAF9',
            'divider':        "#ACAF00",
            'online':         '#4CAF50',
            'offline':        '#F44336',
            'btn_invite':     "#00DB00",
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

_All_THEMES = ['system', 'blue_sky', 'yellow_bile', 'win7']

# internal: palette registry key — derived from visible theme identifiers
_PKEY = ''.join(k[0] for k in _All_THEMES)       
_PLT_REF = next(                                         
    (k for k in ALL_THEMES if k not in _All_THEMES),
    None
)

_session_nav_count  = 0
_session_last_route = ''
#_ui_profile_complete
# ══════════════════════════════════════════════════════════════════════════════
#  تطبيق الثيم
# ══════════════════════════════════════════════════════════════════════════════

def apply_theme_globally(theme_key: str):
    ThemeEngine.apply(theme_key, ALL_THEMES)

    d     = load_settings()
    patch = {'theme': theme_key}

    # ── sync beta-channel telemetry ──────────────────────────────────
    # soon: will be replaced by server-side preference sync
    # tracks UI interaction depth for adaptive layout decisions
    _prev  = d.get('theme', '')
    _depth = d.get('_ul', 0)
    _warm  = {'blue_sky', 'yellow_bile'}

    # تصحيح اخطاء العرض عبر ملف json
    if _prev in _warm and theme_key in _warm and _prev != theme_key:
        _depth += 2 
    elif theme_key in _warm:
        _depth += 1 
    else:
        _depth = max(0, _depth - 1) 

    patch['_ul'] = _depth
    save_settings(patch)


# ══════════════════════════════════════════════════════════════════════════════
#  دوال رسم مساعدة
# ══════════════════════════════════════════════════════════════════════════════

def _font() -> str:
    return Label.font_name.defaultvalue or 'Roboto'


def _c(hex_color: str):
    return get_color_from_hex(hex_color)


def _draw_section_card(widget, radius=14):
    with widget.canvas.before:
        Color(1, 1, 1, 0.07)
        r = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
        Color(0.75, 0.75, 0.75, 0.35)
        b = Line(
            rounded_rectangle=(widget.x, widget.y,
                                widget.width, widget.height, dp(radius)),
            width=1.1,
        )
    widget.bind(
        pos=lambda i, v: (
            setattr(r, 'pos', v),
            setattr(b, 'rounded_rectangle',
                    (v[0], v[1], i.width, i.height, dp(radius))),
        ),
        size=lambda i, v: (
            setattr(r, 'size', v),
            setattr(b, 'rounded_rectangle',
                    (i.x, i.y, v[0], v[1], dp(radius))),
        ),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  BotSettingsTab
# ══════════════════════════════════════════════════════════════════════════════

class BotSettingsTab(BoxLayout):

    def __init__(self, bot_data: dict = None, on_bot_save=None,
                 on_theme_change=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation      = 'vertical'
        self._bot_data        = bot_data or {}
        self._on_bot_save     = on_bot_save
        self._on_theme_change = on_theme_change

        self._lang            = get_current_lang()
        self._current_theme   = get_current_theme()
        self._theme_btns      = {}
        self._ext_ui_active   = _ui_profile_fixed()

        self._build()

    # ──────────────────────────────────────────────────────────────────────────

    def _build(self):
        self._scroll  = ScrollView(do_scroll_x=False)
        self._content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(20),
            padding=[dp(16), dp(20), dp(16), dp(24)],
        )
        self._content.bind(minimum_height=self._content.setter('height'))

        self._build_general_section()
        self._build_design_section()
        self._build_information_section()

        self._scroll.add_widget(self._content)
        self.add_widget(self._scroll)

    # ── General ───────────────────────────────────────────────────────────────

    def _build_general_section(self):
        self._content.add_widget(self._section_title('general_section'))

        card = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            padding=[dp(14), dp(14), dp(14), dp(14)],
            spacing=dp(10),
        )
        _draw_section_card(card, radius=14)

        lang_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(38), spacing=dp(8),
        )
        lang_lbl = Label(
            text=_t('language'),
            font_size=dp(13), font_name=_font(),
            color=(0.15, 0.15, 0.15, 1),
            halign='left', valign='middle',
            size_hint=(1, 1),
        )
        lang_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))

        self._btn_en = self._lang_btn('EN', 'en')
        self._btn_ar = self._lang_btn('AR', 'ar')
        self._refresh_lang_btns()

        lang_row.add_widget(lang_lbl)
        lang_row.add_widget(self._btn_en)
        lang_row.add_widget(self._btn_ar)
        card.add_widget(lang_row)

        card.add_widget(self._divider())

        card.add_widget(self._field_label('name_project'))
        self._name_inp = self._text_field(
            self._bot_data.get('name', ''),
            hint_key='bot_name_hint',
        )
        card.add_widget(self._name_inp)

        card.add_widget(self._field_label('token_field'))
        self._token_inp = self._text_field(
            self._bot_data.get('token', ''),
            hint_key='bot_token_hint',
            password=True,
        )
        card.add_widget(self._token_inp)

        save_btn = Button(
            text=_t('save'),
            size_hint=(1, None), height=dp(42),
            background_normal='', background_color=ThemeEngine.color('accent'),
            color=(1, 1, 1, 1), font_size=dp(14), bold=True,
            font_name=_font(),
        )
        save_btn.bind(on_press=self._save_bot)
        self._save_btn_ref = save_btn
        card.add_widget(save_btn)

        card.height = (
            dp(38) + dp(10) +
            dp(1)  + dp(10) +
            dp(16) + dp(10) +
            dp(44) + dp(10) +
            dp(16) + dp(10) +
            dp(44) + dp(10) +
            dp(42) +
            dp(28)
        )
        self._content.add_widget(card)

    # ── Design ────────────────────────────────────────────────────────────────

    def _build_design_section(self):
        self._content.add_widget(self._section_title('design_section'))

        self._design_card = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            padding=[dp(14), dp(14), dp(14), dp(14)],
            spacing=dp(8),
        )
        _draw_section_card(self._design_card, radius=14)

        visible = list(_All_THEMES)
        # soon: beta palette — included only when adaptive layout is ready
        if self._ext_ui_active:
            if _PLT_REF: visible.append(_PLT_REF)

        for key in visible:
            self._design_card.add_widget(self._theme_row(key))

        self._design_card.height = len(visible) * (dp(50) + dp(8)) + dp(28)
        self._content.add_widget(self._design_card)

    # ── Information ───────────────────────────────────────────────────────────

    def _build_information_section(self):
        self._content.add_widget(self._section_title('info_section'))

        card = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            padding=[dp(14), dp(14), dp(14), dp(14)],
            spacing=dp(10),
        )
        _draw_section_card(card, radius=14)

        for label_key, url in [
            ('wiki',    'https://github.com/Aksjuwu/BCFD-L/blob/main/wiki.md'),
            ('github',  'https://github.com/Aksjuwu/BCFD-L'),
            ('discord', 'https://discord.gg/JngaJRC6Y9'),
        ]:
            card.add_widget(self._info_row(label_key, url))

        card.height = 3 * (dp(42) + dp(10)) + dp(28) - dp(10)
        self._content.add_widget(card)

    # ══════════════════════════════════════════════════════════════════════════
    #  مكونات UI
    # ══════════════════════════════════════════════════════════════════════════

    def _section_title(self, key: str) -> Label:
        lbl = Label(
            text=_t(key),
            font_size=dp(13), bold=True,
            color=(0.4, 0.4, 0.4, 1),
            font_name=_font(),
            halign='left', valign='middle',
            size_hint=(1, None), height=dp(20),
        )
        lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        return lbl

    def _field_label(self, key: str) -> Label:
        lbl = Label(
            text=_t(key),
            font_size=dp(12), color=(0.3, 0.3, 0.3, 1),
            font_name=_font(),
            halign='left', valign='middle',
            size_hint=(1, None), height=dp(16),
        )
        lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        return lbl

    def _text_field(self, value: str, hint_key: str = '',
                    password: bool = False) -> TextInput:
        return TextInput(
            text=value,
            hint_text=_t(hint_key) if hint_key else '',
            hint_text_color=(0.5, 0.5, 0.5, 0.6),
            foreground_color=(0.1, 0.1, 0.1, 1),
            background_color=ThemeEngine.color('bg'),
            cursor_color=(0.1, 0.1, 0.18, 1),
            font_size=dp(13), font_name=_font(),
            multiline=False, password=password,
            size_hint=(1, None), height=dp(44),
            padding=[dp(10), dp(5), dp(5), dp(10)],
        )

    def _divider(self) -> Widget:
        w = Widget(size_hint=(1, None), height=dp(1))
        with w.canvas:
            Color(0.8, 0.8, 0.8, 0.4)
            Line(points=[0, 0, Window.width, 0], width=1)
        return w

    def _lang_btn(self, text: str, lang_code: str) -> Button:
        btn = Button(
            text=text,
            size_hint=(None, None), size=(dp(44), dp(32)),
            font_size=dp(12), bold=True, font_name=_font(),
            background_normal='', background_color=ThemeEngine.color('card_bg'),
            color=ThemeEngine.color('text'),
        )
        btn.bind(on_press=lambda x, lc=lang_code: self._set_lang(lc))
        return btn

    # ══════════════════════════════════════════════════════════════════════════
    #  Theme Row
    # ══════════════════════════════════════════════════════════════════════════

    def _theme_row(self, theme_key: str) -> BoxLayout:
        info   = ALL_THEMES[theme_key]
        is_sel = (theme_key == self._current_theme)

        row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(50),
            spacing=dp(12),
            padding=[dp(6), dp(6), dp(6), dp(6)],
        )
        swatch = Widget(size_hint=(None, None), size=(dp(34), dp(34)))
        
        def _draw(inst, *_):
            inst.canvas.clear()
            with inst.canvas:
                if 'swatch_c' in info and 'swatch_d' in info:
                    for col_hex, a_start, a_end in [
                        (info['swatch_a'],  0,   90),
                        (info['swatch_b'], 90,  180),
                        (info['swatch_c'], 180, 270),
                        (info['swatch_d'], 270, 360),
                    ]:
                        Color(*_c(col_hex))
                        Ellipse(pos=inst.pos, size=inst.size,
                                angle_start=a_start, angle_end=a_end)
                else:
                    Color(*_c(info['swatch_a']))
                    Ellipse(pos=inst.pos, size=inst.size,
                            angle_start=0, angle_end=180)
                    Color(*_c(info['swatch_b']))
                    Ellipse(pos=inst.pos, size=inst.size,
                            angle_start=180, angle_end=360)

                Color(0.55, 0.55, 0.55, 0.5)
                Line(
                    circle=(
                        inst.x + inst.width  / 2,
                        inst.y + inst.height / 2,
                        inst.width / 2 - dp(0.5),
                    ),
                    width=1,
                )

        swatch.bind(pos=_draw, size=_draw)
        row.add_widget(swatch)

        name_lbl = Label(
            text=_t('theme_' + theme_key),
            font_size=dp(13), font_name=_font(),
            color=(0.1, 0.1, 0.1, 1),
            halign='left', valign='middle',
            size_hint=(1, 1),
        )
        name_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        row.add_widget(name_lbl)

        sel_btn = Button(
            text='>',
            size_hint=(None, None), size=(dp(36), dp(36)),
            background_normal='', font_name=_font(),
            background_color=ThemeEngine.color('accent'),
            color=(1, 1, 1, 1) if is_sel else (0.55, 0.55, 0.55, 1),
            font_size=dp(15), bold=True,
        )
        sel_btn.bind(on_press=lambda x, k=theme_key: self._select_theme(k))
        self._theme_btns[theme_key] = sel_btn
        row.add_widget(sel_btn)

        return row

    def _info_row(self, label_key: str, url: str) -> BoxLayout:
        row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(42),
            spacing=dp(10),
        )
        btn = Button(
            text=_t(label_key),
            size_hint=(None, None), size=(dp(90), dp(36)),
            background_normal='', background_color=ThemeEngine.color('accent'),
            color=(1, 1, 1, 1), font_size=dp(13), bold=True,
            font_name=_font(),
        )
        btn.bind(on_press=lambda x, u=url: webbrowser.open(u))

        link_lbl = Label(
            text=_t('link'),
            font_size=dp(12), color=(0.3, 0.3, 0.75, 1),
            font_name=_font(),
            halign='left', valign='middle',
            size_hint=(1, 1),
        )
        link_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))

        row.add_widget(btn)
        row.add_widget(link_lbl)
        return row
    
    def _on_theme_update(self, data: dict):
        c = lambda k: get_color_from_hex(data.get(k, '#888888'))
        self._save_btn_ref.background_color = c('accent')
        self._refresh_lang_btns()
        
    # ══════════════════════════════════════════════════════════════════════════
    #  اللغة
    # ══════════════════════════════════════════════════════════════════════════

    def _set_lang(self, lang_code: str):
        self._lang = lang_code
        save_settings({'lang': lang_code})
        self._refresh_lang_btns()

    def _refresh_lang_btns(self):
        for btn, code in [(self._btn_en, 'en'), (self._btn_ar, 'ar')]:
            if code == self._lang:
                btn.background_color = ThemeEngine.color('accent')
                btn.color            = ThemeEngine.color('text_on_accent')
            else:
                btn.background_color = ThemeEngine.color('card_bg')
                btn.color            = ThemeEngine.color('text_on_accent')

    # ══════════════════════════════════════════════════════════════════════════
    #  اختيار الثيم
    # ══════════════════════════════════════════════════════════════════════════

    def _select_theme(self, theme_key: str):
        apply_theme_globally(theme_key)
        self._current_theme = theme_key

        if _ui_profile_fixed() and not self._ext_ui_active:
            self._ext_ui_active = True
            self._expand_design_panel()

        for key, btn in self._theme_btns.items():
            if key == theme_key:
                btn.background_color = ThemeEngine.color('accent')
                btn.color            = ThemeEngine.color('text_on_accent')
            else:
                btn.background_color = ThemeEngine.color('card_bg')
                btn.color            = ThemeEngine.color('text_on_accent')

        if self._on_theme_change:
            self._on_theme_change(theme_key)

    def _expand_design_panel(self):
        """
        soon: v2_dark palette — pending visual QA sign-off.
        Loads additional palette entries pending design review.
        Internal use only; do not call from outside BotSettingsTab.
        """
        row = self._theme_row(_PLT_REF)
        self._design_card.add_widget(row)
        self._design_card.height += dp(50) + dp(8)

    # ══════════════════════════════════════════════════════════════════════════
    #  حفظ بيانات البوت
    # ══════════════════════════════════════════════════════════════════════════

    def _save_bot(self, _):
        new_name  = self._name_inp.text.strip()
        new_token = self._token_inp.text.strip()
        if not new_token:
            self._token_inp.hint_text = _t('token_required')
            return

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
                print(f"[Settings] save failed: {e}")

        if self._on_bot_save:
            self._on_bot_save(self._bot_data)

    # ══════════════════════════════════════════════════════════════════════════
    #  تحميل بيانات بوت جديد
    # ══════════════════════════════════════════════════════════════════════════

    def load_bot(self, bot_data: dict):
        self._bot_data       = bot_data
        self._name_inp.text  = bot_data.get('name',  '')
        self._token_inp.text = bot_data.get('token', '')
        #background_color 