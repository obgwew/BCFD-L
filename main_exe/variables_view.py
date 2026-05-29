# -*- coding: utf-8 -*-
# main_exe/variables_view.py

import os
import json

from kivy.uix.boxlayout          import BoxLayout
from kivy.uix.floatlayout        import FloatLayout
from kivy.uix.scrollview         import ScrollView
from kivy.uix.gridlayout         import GridLayout
from kivy.uix.label              import Label
from kivy.uix.button             import Button
from kivy.uix.textinput          import TextInput
from kivy.uix.widget             import Widget
from kivy.metrics                import dp
from kivy.utils                  import get_color_from_hex
from kivy.graphics               import Color, RoundedRectangle, Line, Ellipse

from main_exe.langs.translations import Translations
from main_exe.settings           import get_current_lang
from main_exe.theme_engine       import ThemeEngine


# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _t(key: str) -> str:
    return Translations.get(key, get_current_lang())

def _font() -> str:
    return Label.font_name.defaultvalue or 'Roboto'

def _c(key: str):
    return ThemeEngine.color(key)

def _draw_card(widget, radius: int = 12):
    with widget.canvas.before:
        Color(*_c('card_bg'))
        _r = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
        Color(*_c('card_border'))
        _b = Line(
            rounded_rectangle=(widget.x, widget.y,
                                widget.width, widget.height, dp(radius)),
            width=1.1,
        )
    widget.bind(
        pos=lambda i, v: (
            setattr(_r, 'pos', v),
            setattr(_b, 'rounded_rectangle',
                    (v[0], v[1], i.width, i.height, dp(radius))),
        ),
        size=lambda i, v: (
            setattr(_r, 'size', v),
            setattr(_b, 'rounded_rectangle',
                    (i.x, i.y, v[0], v[1], dp(radius))),
        ),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  Storage helpers
# ══════════════════════════════════════════════════════════════════════════════

def _bot_root_from_dir(bot_dir: str) -> str:
    return os.path.dirname(os.path.abspath(bot_dir))

def _vars_dir(bot_dir: str) -> str:
    return os.path.join(_bot_root_from_dir(bot_dir), 'bot_vars')

def _ensure_vars_dir(bot_dir: str) -> str:
    path = _vars_dir(bot_dir)
    os.makedirs(path, exist_ok=True)
    return path

def _var_path(bot_dir: str, name: str) -> str:
    safe = ''.join(c for c in name if c.isalnum() or c in ('-', '_')).strip() or 'var'
    return os.path.join(_vars_dir(bot_dir), f'{safe}.json')

def _load_all_vars(bot_dir: str) -> list:
    d = _vars_dir(bot_dir)
    if not os.path.isdir(d):
        return []
    result = []
    for fname in sorted(os.listdir(d)):
        if not fname.endswith('.json'):
            continue
        fpath = os.path.join(d, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                data['_path'] = fpath
                result.append(data)
        except Exception as e:
            print(f'[Variables] load error {fpath}: {e}')
    return result

def _write_var(bot_dir: str, name: str, value: str, old_path: str = '') -> str:
    new_path = _var_path(bot_dir, name)
    if old_path and os.path.abspath(old_path) != os.path.abspath(new_path):
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass
    _ensure_vars_dir(bot_dir)
    with open(new_path, 'w', encoding='utf-8') as f:
        json.dump({'name': name, 'value': value}, f, ensure_ascii=False, indent=2)
    print(f'[Variables] saved → {new_path}')
    return new_path

def _delete_var(path: str):
    if os.path.isfile(path):
        try:
            os.remove(path)
            print(f'[Variables] deleted → {path}')
        except Exception as e:
            print(f'[Variables] delete error: {e}')


# ══════════════════════════════════════════════════════════════════════════════
#  BotVariablesTab
# ══════════════════════════════════════════════════════════════════════════════

class BotVariablesTab(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation   = 'vertical'
        self._bot_dir      = ''
        self._variables    = []
        self._edit_path    = ''
        self._current_view = 'list'
        self._build()
        ThemeEngine.subscribe(self._on_theme)

    # ══════════════════════════════════════════════════════════════════════════
    #  Theme callback
    # ══════════════════════════════════════════════════════════════════════════

    def _on_theme(self, data: dict):
        c = lambda k: get_color_from_hex(data.get(k, '#888888'))

        # ── List view widgets ─────────────────────────────────────────
        self._empty_lbl.color             = c('text_dim')

        # search box
        self._search_inp.background_color = c('card_bg')
        self._search_inp.foreground_color = c('text')
        self._search_inp.cursor_color     = c('accent')
        self._search_bg_color.rgba        = list(c('card_bg'))
        self._search_bd_color.rgba        = list(c('card_border'))

        # FAB
        self._fab_color.rgba              = list(c('accent'))

        # ── Editor view widgets ───────────────────────────────────────
        self._editor_title.color          = c('text')
        self._del_bg_color.rgba           = list(c('danger'))
        self._back_btn.background_color   = c('accent')
        self._name_lbl.color              = c('text')
        self._value_lbl.color             = c('text')
        self._name_inp.background_color   = c('card_bg')
        self._name_inp.foreground_color   = c('text')
        self._name_inp.cursor_color       = c('accent')
        self._value_inp.background_color  = c('card_bg')
        self._value_inp.foreground_color  = c('text')
        self._value_inp.cursor_color      = c('accent')
        self._save_bg_color.rgba          = list(c('accent'))

        # إعادة رسم القائمة بألوان الثيم الجديد
        if self._current_view == 'list':
            self._refresh_list()

    # ══════════════════════════════════════════════════════════════════════════
    #  Storage
    # ══════════════════════════════════════════════════════════════════════════

    def _load_variables(self):
        if self._bot_dir:
            self._variables = _load_all_vars(self._bot_dir)
        else:
            self._variables = []

    # ══════════════════════════════════════════════════════════════════════════
    #  Build
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        self._list_root   = self._build_list_view()
        self._editor_root = self._build_editor_view()
        self._show_list()

    # ──────────────────────────────────────────────────────────────────────────
    #  List View
    # ──────────────────────────────────────────────────────────────────────────

    def _build_list_view(self) -> FloatLayout:
        root = FloatLayout()

        # Header
        header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(52),
            pos_hint={'top': 1},
            padding=[dp(16), dp(9), dp(16), dp(9)],
            spacing=dp(8),
        )
        title_lbl = Label(
            text=_t('variables'),
            font_size=dp(20), bold=True,
            color=_c('text'), font_name=_font(),
            size_hint=(None, 1), width=dp(120),
            halign='left', valign='middle',
        )
        title_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        header.add_widget(title_lbl)
        header.add_widget(Widget(size_hint_x=1))

        # Search input — تم توسيع الحقل إلى 180dp لتعويض مكان الزر المحذوف
        self._search_inp = TextInput(
            hint_text='Search...',
            hint_text_color=(0.5, 0.5, 0.5, 0.55),
            foreground_color=_c('text'),
            background_color=(0, 0, 0, 0),
            cursor_color=_c('accent'),
            font_size=dp(13), font_name=_font(),
            multiline=False,
            size_hint=(None, None), size=(dp(180), dp(34)),
            padding=[dp(10), dp(8)],
        )
        with self._search_inp.canvas.before:
            self._search_bg_color = Color(*_c('card_bg'))
            _sbg = RoundedRectangle(
                pos=self._search_inp.pos,
                size=self._search_inp.size,
                radius=[dp(8)],
            )
            self._search_bd_color = Color(*_c('card_border'))
            _sbd = Line(
                rounded_rectangle=(
                    self._search_inp.x, self._search_inp.y,
                    self._search_inp.width, self._search_inp.height, dp(8),
                ),
                width=1.1,
            )
        self._search_inp.bind(
            pos=lambda i, v: (
                setattr(_sbg, 'pos', v),
                setattr(_sbd, 'rounded_rectangle',
                        (v[0], v[1], i.width, i.height, dp(8))),
            ),
            size=lambda i, v: (
                setattr(_sbg, 'size', v),
                setattr(_sbd, 'rounded_rectangle',
                        (i.x, i.y, v[0], v[1], dp(8))),
            ),
        )
        self._search_inp.bind(text=lambda i, v: self._refresh_list())
        header.add_widget(self._search_inp)

        # ScrollView / Grid
        sv = ScrollView(
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}, do_scroll_x=False,
        )
        self._grid = GridLayout(
            cols=1, spacing=dp(8), size_hint_y=None,
            padding=[dp(14), dp(58), dp(14), dp(68)],
        )
        self._grid.bind(minimum_height=self._grid.setter('height'))
        sv.add_widget(self._grid)
        
        # ترتيب الإضافة هنا جوهري: ScrollView أولاً ثم Header فوقه لضمان استجابة اللمس والكتابة
        root.add_widget(sv)
        root.add_widget(header)

        # Empty state
        self._empty_lbl = Label(
            text=_t('no_variables'),
            font_size=dp(14), color=_c('text_dim'),
            font_name=_font(), halign='center',
            size_hint=(None, None), size=(dp(260), dp(40)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5},
        )
        self._empty_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        root.add_widget(self._empty_lbl)

        # FAB (+) — نحفظ Color كـ self._fab_color
        fab = Button(
            text='+',
            size_hint=(None, None), size=(dp(52), dp(52)),
            pos_hint={'right': 0.95, 'y': 0.04},
            background_normal='', background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1), font_size=dp(28), bold=True,
            font_name=_font(),
        )
        with fab.canvas.before:
            self._fab_color = Color(*_c('accent'))
            self._fab_ellipse = Ellipse(pos=fab.pos, size=fab.size)
        fab.bind(
            pos=lambda i, v: setattr(self._fab_ellipse, 'pos', v),
            size=lambda i, v: setattr(self._fab_ellipse, 'size', v),
        )
        fab.bind(on_press=lambda x: self._open_editor(''))
        root.add_widget(fab)

        return root

    # ──────────────────────────────────────────────────────────────────────────
    #  Editor View
    # ──────────────────────────────────────────────────────────────────────────

    def _build_editor_view(self) -> BoxLayout:
        root = BoxLayout(
            orientation='vertical',
            padding=[dp(20), dp(18), dp(20), dp(16)],
            spacing=dp(10),
        )

        # Title row
        title_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(42),
            spacing=dp(10),
        )

        # زر الحذف — نحفظ Color كـ self._del_bg_color
        self._del_btn = Button(
            text='X',
            size_hint=(None, None), size=(dp(36), dp(36)),
            background_normal='', background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1), font_size=dp(13), bold=True,
            font_name=_font(),
        )
        with self._del_btn.canvas.before:
            self._del_bg_color = Color(*_c('danger'))
            _dc = Ellipse(pos=self._del_btn.pos, size=self._del_btn.size)
        self._del_btn.bind(
            pos=lambda i, v: setattr(_dc, 'pos', v),
            size=lambda i, v: setattr(_dc, 'size', v),
        )
        self._del_btn.bind(on_press=self._delete_variable)
        title_row.add_widget(self._del_btn)

        self._editor_title = Label(
            text='Variables / new.json',
            font_size=dp(14), bold=True,
            color=_c('text'), font_name=_font(),
            halign='left', valign='middle',
            size_hint=(1, 1),
        )
        self._editor_title.bind(size=lambda i, v: setattr(i, 'text_size', v))
        title_row.add_widget(self._editor_title)

        self._back_btn = Button(
            text='←',
            size_hint=(None, None), size=(dp(36), dp(36)),
            background_normal='', background_color=_c('accent'),
            color=(1, 1, 1, 1), font_size=dp(18), font_name=_font(),
        )
        self._back_btn.bind(on_press=lambda x: self._show_list())
        title_row.add_widget(self._back_btn)
        root.add_widget(title_row)

        # حقل الاسم
        self._name_lbl = self._editor_label(_t('variable_name'))
        root.add_widget(self._name_lbl)
        self._name_inp = self._editor_field('exp: (wew)')
        root.add_widget(self._name_inp)

        # حقل القيمة
        self._value_lbl = self._editor_label(_t('variable_value'))
        root.add_widget(self._value_lbl)
        self._value_inp = self._editor_field('exp: (1,2,3...)')
        root.add_widget(self._value_inp)

        root.add_widget(Widget(size_hint_y=1))

        # زر الحفظ — نحفظ Color كـ self._save_bg_color
        save_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(50),
        )
        save_row.add_widget(Widget(size_hint_x=1))
        save_btn = Button(
            text=_t('save'),
            size_hint=(None, None), size=(dp(110), dp(44)),
            background_normal='', background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1), font_size=dp(15), bold=True,
            font_name=_font(),
        )
        with save_btn.canvas.before:
            self._save_bg_color = Color(*_c('accent'))
            _sv = RoundedRectangle(pos=save_btn.pos, size=save_btn.size, radius=[dp(22)])
        save_btn.bind(
            pos=lambda i, v: setattr(_sv, 'pos', v),
            size=lambda i, v: setattr(_sv, 'size', v),
        )
        save_btn.bind(on_press=self._save_variable)
        save_row.add_widget(save_btn)
        root.add_widget(save_row)

        return root

    def _editor_label(self, text: str) -> Label:
        lbl = Label(
            text=text, font_size=dp(15), bold=True,
            color=_c('text'), font_name=_font(),
            halign='left', valign='middle',
            size_hint=(1, None), height=dp(28),
        )
        lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        return lbl

    def _editor_field(self, hint: str) -> TextInput:
        return TextInput(
            hint_text=hint,
            hint_text_color=(0.5, 0.5, 0.5, 0.5),
            foreground_color=_c('text'),
            background_color=_c('card_bg'),
            cursor_color=_c('accent'),
            font_size=dp(14), font_name=_font(),
            multiline=False,
            size_hint=(1, None), height=dp(46),
            padding=[dp(12), dp(10)],
        )

    # ══════════════════════════════════════════════════════════════════════════
    #  View Switching
    # ══════════════════════════════════════════════════════════════════════════

    def _show_list(self):
        self.clear_widgets()
        self._load_variables()
        self._refresh_list()
        self.add_widget(self._list_root)
        self._current_view = 'list'

    def _open_editor(self, var_path: str):
        self._edit_path = var_path
        if not var_path:
            self._name_inp.text     = ''
            self._value_inp.text    = ''
            self._editor_title.text = 'Variables / new.json'
            self._del_btn.opacity   = 0
            self._del_btn.disabled  = True
        else:
            var  = next((v for v in self._variables if v.get('_path') == var_path), {})
            name = var.get('name', '')
            self._name_inp.text     = name
            self._value_inp.text    = var.get('value', '')
            self._editor_title.text = f'Variables / {name}.json'
            self._del_btn.opacity   = 1
            self._del_btn.disabled  = False
        self.clear_widgets()
        self.add_widget(self._editor_root)
        self._current_view = 'editor'

    # ══════════════════════════════════════════════════════════════════════════
    #  List
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_list(self):
        self._grid.clear_widgets()
        q = self._search_inp.text.strip().lower()
        filtered = [
            v for v in self._variables
            if not q
            or q in v.get('name',  '').lower()
            or q in v.get('value', '').lower()
        ]
        self._empty_lbl.opacity = 0 if filtered else 1
        for num, var in enumerate(filtered, start=1):
            self._grid.add_widget(self._var_card(num, var))

    def _var_card(self, num: int, var: dict) -> BoxLayout:
        row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(56),
            spacing=dp(8),
        )
        num_lbl = Label(
            text=str(num),
            font_size=dp(17), bold=True,
            color=_c('text_dim'), font_name=_font(),
            size_hint=(None, 1), width=dp(26),
            halign='center', valign='middle',
        )
        num_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        row.add_widget(num_lbl)

        card = Button(
            text=f"N=({var.get('name', '')})  |  V=({var.get('value', '')})",
            font_size=dp(13), font_name=_font(),
            color=_c('text'),
            background_normal='', background_color=(0, 0, 0, 0),
            halign='left', valign='middle',
            size_hint=(1, 1),
            padding=[dp(12), 0],
        )
        card.bind(size=lambda i, v: setattr(i, 'text_size', (v[0] - dp(24), v[1])))
        _draw_card(card, radius=10)
        vpath = var.get('_path', '')
        card.bind(on_press=lambda x, p=vpath: self._open_editor(p))
        row.add_widget(card)
        return row

    # ══════════════════════════════════════════════════════════════════════════
    #  Editor Operations
    # ══════════════════════════════════════════════════════════════════════════

    def _save_variable(self, _):
        name  = self._name_inp.text.strip()
        value = self._value_inp.text.strip()
        if not name:
            self._name_inp.hint_text = _t('enter_variable_name')
            return
        if not self._bot_dir:
            print('[Variables] bot_dir not set')
            return
        _write_var(self._bot_dir, name, value, self._edit_path)
        self._show_list()

    def _delete_variable(self, _):
        if self._edit_path:
            _delete_var(self._edit_path)
        self._show_list()

    # ══════════════════════════════════════════════════════════════════════════
    #  Public API
    # ══════════════════════════════════════════════════════════════════════════

    def load_bot(self, bot_dir: str):
        self._bot_dir = bot_dir
        self._load_variables()
        if self._current_view == 'list':
            self._refresh_list()