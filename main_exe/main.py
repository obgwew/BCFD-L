# -*- coding: utf-8 -*-
# main_exe/main.py

import os
import json
import base64
import webbrowser

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse

from main_exe.settings import BotSettingsTab, get_current_lang
from main_exe.commands_view import BotCommandsTab
from main_exe.langs.translations import Translations
from main_exe.theme_engine import ThemeEngine
from main_exe.variables_view import BotVariablesTab

Window.icon = "main_exe/icons/BCFD.ico"

NEW_TXT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'main_exe/new.txt'
)

# ══════════════════════════════════════════════════════════════════════════════
#  TRANSLATION HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _t(key: str) -> str:
    return Translations.get(key, get_current_lang())


# ══════════════════════════════════════════════════════════════════════════════
#  THEME  —  يُحدَّث من ThemeEngine.apply() مباشرة بدون إعادة تشغيل
# ══════════════════════════════════════════════════════════════════════════════

THEME = {
    'bg':           '#FFFFFF',
    'card_bg':      '#FFFFFF',
    'card_border':  '#E0E0E0',
    'nav_bg':       '#C1CFFF',
    'nav_active':   '#000000',
    'nav_inactive': '#000000',
    'accent':       '#1B1F2E',
    'success':      '#16A34A',
    'danger':       '#DC2626',
    'text':         '#1D242E',
    'text_dim':     '#151A1F',
    'divider':      '#E4E8F0',
    'online':       '#16A34A',
    'offline':      '#DC2626',
    'btn_invite':   '#5865F2',
}


def _font() -> str:
    return Label.font_name.defaultvalue or 'Roboto'


def _c(key: str):
    return get_color_from_hex(THEME.get(key, '#888888'))


# ── إعادة رسم خلفية card عند تغيير الثيم ────────────────────────────────────
def _card(widget, radius=14):
    with widget.canvas.before:
        Color(*_c('card_bg'))
        r = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
        Color(*_c('card_border'))
        b = Line(
            rounded_rectangle=(widget.x, widget.y,
                                widget.width, widget.height, dp(radius)),
            width=1.1,
        )
    widget.bind(
        pos =lambda i, v: (
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
    # نُعيد الـ refs لإمكانية تحديثها لاحقاً
    return r, b


def _get_bot_id_from_token(token: str) -> str:
    try:
        part1   = token.split('.')[0]
        padding = 4 - len(part1) % 4
        if padding != 4:
            part1 += '=' * padding
        return base64.b64decode(part1).decode('utf-8')
    except Exception:
        return ''


def _read_new_txt() -> str:
    path = os.path.normpath(NEW_TXT_PATH)
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            return text if text else _t('no_updates')
        except Exception:
            return _t('read_error')
    return _t('no_file')


# ══════════════════════════════════════════════════════════════════════════════
#  BotMainTab
# ══════════════════════════════════════════════════════════════════════════════

class BotMainTab(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation    = 'vertical'
        self._server_online = False
        self._bot_data      = {}
        self._build()
        # التسجيل في ThemeEngine — يُستدعى تلقائياً عند كل تغيير ثيم
        ThemeEngine.subscribe(self._on_theme)

    # ──────────────────────────────────────────────────────────────────────────

    def _build(self):
        self._scroll  = ScrollView(do_scroll_x=False)
        self._content = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            spacing=dp(16),
            padding=[dp(20), dp(24), dp(20), dp(20)],
        )
        self._content.bind(minimum_height=self._content.setter('height'))

        # ── صورة البوت ───────────────────────────────────────────────
        avatar_wrap = BoxLayout(
            size_hint=(1, None), height=dp(110),
            orientation='horizontal',
        )
        avatar_wrap.add_widget(Widget())

        self._avatar = Label(
            text=_t('avatar_none'),
            font_size=dp(13), font_name=_font(),
            color=_c('text_dim'),
            size_hint=(None, None), size=(dp(96), dp(96)),
            halign='center', valign='middle',
        )
        with self._avatar.canvas.before:
            Color(*_c('card_border'))
            self._avatar_circle = Ellipse(
                pos=self._avatar.pos, size=self._avatar.size)
        self._avatar.bind(
            pos =lambda i, v: setattr(self._avatar_circle, 'pos',  v),
            size=lambda i, v: setattr(self._avatar_circle, 'size', v),
        )
        avatar_wrap.add_widget(self._avatar)
        avatar_wrap.add_widget(Widget())
        self._content.add_widget(avatar_wrap)

        # ── اسم البوت ────────────────────────────────────────────────
        self._name_lbl = Label(
            text='', font_size=dp(18), bold=True,
            color=_c('text'), font_name=_font(),
            size_hint=(1, None), height=dp(28),
            halign='center', valign='middle',
        )
        self._name_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        self._content.add_widget(self._name_lbl)

        # ── زر Invite Bot ────────────────────────────────────────────
        self._invite_btn = Button(
            text=_t('invite_bot'),
            size_hint=(1, None), height=dp(46),
            background_normal='', background_color=_c('btn_invite'),
            color=(1, 1, 1, 1), font_size=dp(14), bold=True, font_name=_font(),
        )
        self._invite_btn.bind(on_press=self._invite_bot)
        self._content.add_widget(self._invite_btn)

        # ── State Server card ─────────────────────────────────────────
        self._server_card = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(54),
            padding=[dp(14), dp(10), dp(14), dp(10)],
            spacing=dp(12),
        )
        self._server_card_refs = _card(self._server_card, radius=12)

        server_lbl = Label(
            text=_t('state_server'),
            font_size=dp(14), bold=True, color=_c('text'), font_name=_font(),
            halign='left', valign='middle', size_hint=(1, 1),
        )
        server_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        self._server_lbl = server_lbl

        self._state_lbl = Label(
            text=_t('offline'), font_size=dp(13),
            color=_c('offline'), font_name=_font(),
            size_hint=(None, 1), width=dp(90),
            halign='right', valign='middle',
        )
        self._state_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))

        self._server_card.add_widget(server_lbl)
        self._server_card.add_widget(self._state_lbl)
        self._content.add_widget(self._server_card)

        # ── زر On/Off ────────────────────────────────────────────────
        toggle_wrap = BoxLayout(size_hint=(1, None), height=dp(54), orientation='horizontal')
        toggle_wrap.add_widget(Widget())
        self._toggle_btn = Button(
            text=_t('start'),
            size_hint=(None, None), size=(dp(130), dp(44)),
            background_normal='', background_color=_c('success'),
            color=(1, 1, 1, 1), font_size=dp(14), bold=True, font_name=_font(),
        )
        self._toggle_btn.bind(on_press=self._toggle_server)
        toggle_wrap.add_widget(self._toggle_btn)
        toggle_wrap.add_widget(Widget())
        self._content.add_widget(toggle_wrap)

        # ── خط فاصل ──────────────────────────────────────────────────
        divider = Widget(size_hint=(1, None), height=dp(1))
        with divider.canvas:
            Color(*_c('divider'))
            Line(points=[dp(20), 0, Window.width - dp(20), 0], width=1)
        self._content.add_widget(divider)

        # ── What's New ───────────────────────────────────────────────
        self._whats_lbl = Label(
            text=_t('whats_new'), font_size=dp(15), bold=True,
            color=_c('text'), font_name=_font(),
            size_hint=(1, None), height=dp(24),
            halign='left', valign='middle',
        )
        self._whats_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        self._content.add_widget(self._whats_lbl)
        
        # www...
        self._news_box = BoxLayout(
        size_hint=(1, None), height=dp(120),
        padding=[dp(14), dp(12), dp(14), dp(12)],
        )
        self._news_box_refs = _card(self._news_box, radius=12)
        self._news_lbl = Label(
        text=_read_new_txt(), font_size=dp(13),
        color=_c('text_dim'), font_name=_font(),
        halign='left', valign='top',
        size_hint=(1, None),
        )
        self._news_lbl.bind(
        texture_size=lambda i, v: (
            setattr(i, 'height', v[1]),
            setattr(self._news_box, 'height', v[1] + dp(24)),
        )
        )
        self._news_lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        self._news_box.add_widget(self._news_lbl)
        #www
        self._content.add_widget(self._news_box)

        self._scroll.add_widget(self._content)
        self.add_widget(self._scroll)

    # ── تحديث الألوان عند تغيير الثيم ─────────────────────────────────────────

    def _on_theme(self, data: dict):
        """يُستدعى من ThemeEngine عند كل تغيير ثيم — يُحدّث الألوان فوراً."""
        c = lambda k: get_color_from_hex(data.get(k, "#555555"))

        self._name_lbl.color              = c('text')
        self._invite_btn.background_color = c('btn_invite')
        self._server_lbl.color            = c('text')
        self._whats_lbl.color             = c('text')
        self._news_lbl.color              = c('text_dim')

        # حالة الـ toggle تبقى كما هي (online/offline) — نحدث اللون الصحيح
        if self._server_online:
            self._state_lbl.color             = c('online')
            self._toggle_btn.background_color = c('danger')
        else:
            self._state_lbl.color             = c('offline')
            self._toggle_btn.background_color = c('success')

        # إعادة رسم خلفيات الكاردات
        self._redraw_card(self._server_card, data, radius=12)
        self._redraw_card(self._news_box,    data, radius=12)

        # خلفية الـ avatar
        self._avatar.canvas.before.clear()
        with self._avatar.canvas.before:
            Color(*c('card_border'))
            self._avatar_circle = Ellipse(
                pos=self._avatar.pos, size=self._avatar.size)

    @staticmethod
    def _redraw_card(widget, data: dict, radius=12):
        """يُعيد رسم canvas.before لـ card بألوان الثيم الجديد."""
        widget.canvas.before.clear()
        with widget.canvas.before:
            Color(*get_color_from_hex(data.get('card_bg', '#FFFFFF')))
            r = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(radius)])
            Color(*get_color_from_hex(data.get('card_border', '#E0E0E0')))
            b = Line(
                rounded_rectangle=(widget.x, widget.y,
                                   widget.width, widget.height, dp(radius)),
                width=1.1,
            )
        widget.bind(
            pos =lambda i, v: (
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

    # ──────────────────────────────────────────────────────────────────────────

    def load_bot(self, bot_data: dict):
        self._bot_data      = bot_data
        self._server_online = False
        self._name_lbl.text = bot_data.get('name', 'Bot')

        img_path = bot_data.get('image', '')
        self._avatar.canvas.before.clear()
        if img_path and os.path.isfile(img_path):
            self._avatar.text = ''
            with self._avatar.canvas.before:
                Color(*_c('accent'))
                self._avatar_circle = Ellipse(
                    pos=self._avatar.pos, size=self._avatar.size)
            self._avatar.bind(
                pos =lambda i, v: setattr(self._avatar_circle, 'pos',  v),
                size=lambda i, v: setattr(self._avatar_circle, 'size', v),
            )
            parent = self._avatar.parent
            if parent:
                idx = parent.children.index(self._avatar)
                parent.remove_widget(self._avatar)
                self._avatar = Image(
                    source=img_path,
                    size_hint=(None, None), size=(dp(96), dp(96)),
                    fit_mode='contain',
                )
                parent.add_widget(self._avatar, index=idx)
        else:
            self._avatar.text = _t('avatar_none')
            with self._avatar.canvas.before:
                Color(*_c('card_border'))
                self._avatar_circle = Ellipse(
                    pos=self._avatar.pos, size=self._avatar.size)
            self._avatar.bind(
                pos =lambda i, v: setattr(self._avatar_circle, 'pos',  v),
                size=lambda i, v: setattr(self._avatar_circle, 'size', v),
            )

        self._state_lbl.text              = _t('offline')
        self._state_lbl.color             = _c('offline')
        self._toggle_btn.text             = _t('start')
        self._toggle_btn.background_color = _c('success')
        self._news_lbl.text               = _read_new_txt()

    def _invite_bot(self, _):
        token  = self._bot_data.get('token', '')
        bot_id = _get_bot_id_from_token(token)
        if bot_id:
            url = (f'https://discord.com/oauth2/authorize'
                   f'?client_id={bot_id}&permissions=8&scope=bot')
            webbrowser.open(url)

    def _toggle_server(self, _):
        self._server_online = not self._server_online
        if self._server_online:
            self._state_lbl.text              = _t('online')
            self._state_lbl.color             = _c('online')
            self._toggle_btn.text             = _t('stop')
            self._toggle_btn.background_color = _c('danger')
            try:
                from main_exe.core_bcfd import local_server
                local_server.start_bot(self._bot_data.get('bot_dir', ''))
            except Exception as e:
                print(f"[Dashboard] start failed: {e}")
                self._server_online               = False
                self._state_lbl.text              = _t('offline')
                self._state_lbl.color             = _c('offline')
                self._toggle_btn.text             = _t('start')
                self._toggle_btn.background_color = _c('success')
        else:
            self._state_lbl.text              = _t('offline')
            self._state_lbl.color             = _c('offline')
            self._toggle_btn.text             = _t('start')
            self._toggle_btn.background_color = _c('success')
            try:
                from main_exe.core_bcfd import local_server
                local_server.stop_bot()
            except Exception as e:
                print(f"[Dashboard] stop failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  BotDashboardScreen
# ══════════════════════════════════════════════════════════════════════════════

class BotDashboardScreen(Screen):

    def __init__(self, main_screen_manager, **kwargs):
        kwargs.setdefault('name', 'bot_dashboard')
        super().__init__(**kwargs)
        self._main_sm = main_screen_manager
        self._build()
        ThemeEngine.subscribe(self._on_theme)

    # ──────────────────────────────────────────────────────────────────────────

    def _build(self):
        Window.clearcolor = _c('bg')
        root = BoxLayout(orientation='vertical')

        # ── Header ───────────────────────────────────────────────────
        self._header = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(52),
            padding=[dp(14), dp(10), dp(14), dp(10)],
            spacing=dp(10),
        )
        with self._header.canvas.before:
            Color(*_c('card_bg'))
            self._hbg = RoundedRectangle(
                pos=self._header.pos, size=self._header.size, radius=[0])
            Color(*_c('divider'))
            self._hbl = Line(points=[], width=1)
        self._header.bind(
            pos =lambda i, v: (
                setattr(self._hbg, 'pos', v),
                setattr(self._hbl, 'points', [v[0], v[1], v[0]+i.width, v[1]]),
            ),
            size=lambda i, v: (
                setattr(self._hbg, 'size', v),
                setattr(self._hbl, 'points', [i.x, i.y, i.x+v[0], i.y]),
            ),
        )

        self._back_btn = Button(
            text='<- ' + _t('back'),
            size_hint=(None, None), size=(dp(80), dp(34)),
            background_normal='', background_color=_c('accent'),
            color=(1, 1, 1, 1), font_size=dp(12), bold=True, font_name=_font(),
        )
        self._back_btn.bind(on_press=self._go_back)
        self._header.add_widget(self._back_btn)

        self._title_lbl = Label(
            text='', font_size=dp(16), bold=True,
            color=_c('text'), font_name=_font(),
            halign='center', valign='middle', size_hint=(1, 1),
        )
        self._title_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        self._header.add_widget(self._title_lbl)
        self._header.add_widget(Widget(size_hint=(None, 1), width=dp(80)))
        root.add_widget(self._header)

        # ── منطقة المحتوى ────────────────────────────────────────────
        self._content_area = BoxLayout(orientation='vertical', size_hint=(1, 1))
        root.add_widget(self._content_area)

        # ── Bottom Navigation ─────────────────────────────────────────
        self._nav = BoxLayout(orientation='horizontal',
                              size_hint=(1, None), height=dp(64))
        with self._nav.canvas.before:
            Color(*_c('nav_bg'))
            self._nbg = RoundedRectangle(
                pos=self._nav.pos, size=self._nav.size, radius=[dp(0)])
        self._nav.bind(
            pos =lambda i, v: setattr(self._nbg, 'pos', v),
            size=lambda i, v: setattr(self._nbg, 'size', v),
        )
        self._nav_btns = {}
        tabs = [
            ('main',      'main_exe/icons/main.png',      'main_tab'),
            ('commands',  '</>',                           'commands_tab'),
            ('variables', 'main_exe/icons/variables.png', 'variables'),
            ('settings',  'main_exe/icons/settings.png',  'settings'),
        ]
        for tab_id, icon, label_key in tabs:
            wrap = self._make_nav_btn(tab_id, icon, label_key)
            self._nav_btns[tab_id] = wrap
            self._nav.add_widget(wrap)

        root.add_widget(self._nav)
        self.add_widget(root)

        self._main_tab     = BotMainTab()
        self._commands_tab = BotCommandsTab()
        self._settings_tab = BotSettingsTab()
        self._variables_tab = BotVariablesTab()
        
        self._active_tab   = 'main'
        self._switch_tab('main')

    # ── تحديث الألوان عند تغيير الثيم ─────────────────────────────────────────

    def _on_theme(self, data: dict):
        c = lambda k: get_color_from_hex(data.get(k, '#888888'))

        # خلفية التطبيق
        Window.clearcolor = c('bg')

        # Header
        self._header.canvas.before.clear()
        with self._header.canvas.before:
            Color(*c('card_bg'))
            self._hbg = RoundedRectangle(
                pos=self._header.pos, size=self._header.size, radius=[0])
            Color(*c('divider'))
            self._hbl = Line(points=[], width=1)
        self._header.bind(
            pos =lambda i, v: (
                setattr(self._hbg, 'pos', v),
                setattr(self._hbl, 'points', [v[0], v[1], v[0]+i.width, v[1]]),
            ),
            size=lambda i, v: (
                setattr(self._hbg, 'size', v),
                setattr(self._hbl, 'points', [i.x, i.y, i.x+v[0], i.y]),
            ),
        )
        self._back_btn.background_color = c('accent')
        self._title_lbl.color           = c('text')

        # Navigation bar
        self._nav.canvas.before.clear()
        with self._nav.canvas.before:
            Color(*c('nav_bg'))
            self._nbg = RoundedRectangle(
                pos=self._nav.pos, size=self._nav.size, radius=[dp(0)])
        self._nav.bind(
            pos =lambda i, v: setattr(self._nbg, 'pos', v),
            size=lambda i, v: setattr(self._nbg, 'size', v),
        )

        # ألوان أيقونات Nav حسب التاب النشط
        for tid, wrap in self._nav_btns.items():
            col = c('nav_active') if tid == self._active_tab else c('nav_inactive')
            wrap._text_lbl.color = col
            if isinstance(wrap._icon_lbl, Label):
                wrap._icon_lbl.color = col

    # ──────────────────────────────────────────────────────────────────────────

    def _make_nav_btn(self, tab_id: str, icon_path: str, label_key: str):
        wrap = FloatLayout(size_hint=(1, 1))
        box  = BoxLayout(
            orientation='vertical', spacing=dp(2),
            padding=[0, dp(6), 0, dp(4)],
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
        )

        if os.path.isfile(str(icon_path)):
            icon_row = BoxLayout(orientation='horizontal',
                                 size_hint=(1, None), height=dp(28))
            icon_row.add_widget(Widget())
            icon_widget = Image(source=icon_path,
                                size_hint=(None, None), size=(dp(24), dp(24)),
                                fit_mode='contain')
            icon_widget.pos_hint = {'center_y': 0.5}
            icon_row.add_widget(icon_widget)
            icon_row.add_widget(Widget())
            box.add_widget(icon_row)
        else:
            icon_widget = Label(
                text=icon_path, font_size=dp(15), bold=True,
                color=(0, 0, 0, 1), font_name=_font(),
                size_hint=(1, None), height=dp(28),
                halign='center', valign='middle',
            )
            icon_widget.bind(size=lambda i, v: setattr(i, 'text_size', v))
            box.add_widget(icon_widget)

        text_lbl = Label(
            text=_t(label_key), font_size=dp(10),
            color=_c('nav_inactive'), font_name=_font(),
            size_hint=(1, None), height=dp(14),
            halign='center', valign='middle',
        )
        text_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        box.add_widget(text_lbl)

        btn = Button(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
                     background_normal='', background_color=(0, 0, 0, 0))
        btn.bind(on_press=lambda x, tid=tab_id: self._switch_tab(tid))

        wrap.add_widget(box)
        wrap.add_widget(btn)
        wrap._icon_lbl = icon_widget
        wrap._text_lbl = text_lbl
        return wrap

    def _switch_tab(self, tab_id: str):
        self._active_tab = tab_id
        self._content_area.clear_widgets()

        for tid, wrap in self._nav_btns.items():
            col = _c('nav_active') if tid == tab_id else _c('nav_inactive')
            wrap._text_lbl.color = col
            if isinstance(wrap._icon_lbl, Label):
                wrap._icon_lbl.color = col

        if tab_id == 'main':
            self._content_area.add_widget(self._main_tab)
        elif tab_id == 'commands':
            self._content_area.add_widget(self._commands_tab)
        elif tab_id == 'variables':
            self._content_area.add_widget(self._variables_tab)
        elif tab_id == 'settings':
            self._content_area.add_widget(self._settings_tab)

    def load_bot(self, bot_dir: str):
        config_path = os.path.join(bot_dir, 'bot_files', 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                bot_data = json.load(f)
            bot_data['bot_dir'] = bot_dir     
        except Exception as e:
            print(f"[Dashboard] failed to read config.json: {e}")
            bot_data = {}

        self._title_lbl.text = bot_data.get('name', 'Bot')

        bot_files_dir = os.path.join(bot_dir, 'bot_files')
        self._main_tab.load_bot(bot_data)
        self._commands_tab.load_bot(bot_files_dir)
        self._variables_tab.load_bot(bot_files_dir)
        self._settings_tab.load_bot(bot_data)
        self._switch_tab('main')
    
    def _go_back(self, _):
        if self._main_sm and self._main_sm.has_screen('main'):
            self._main_sm.current = 'main'