# -*- coding: utf-8 -*-
# main.py  (root)

import os
import webbrowser
import sys
import json
import shutil
import logging

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image
from plyer import filechooser
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.core.text import LabelBase

from main_exe.langs.translations import Translations
from main_exe.settings import get_current_lang, get_current_theme, apply_theme_globally

logging.getLogger('discord').setLevel(logging.INFO)

import main_exe.core_bcfd.local_server

icon_path = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'main_exe', 'icons', 'BCFD.ico'
)

# ══════════════════════════════════════════════════════════════════════════════
#  TRANSLATION HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _t(key: str) -> str:
    return Translations.get(key, get_current_lang())


# ══════════════════════════════════════════════════════════════════════════════
#  FONTS
# ══════════════════════════════════════════════════════════════════════════════

_FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main_exe', 'langs', 'fonts')
REGISTERED_FONT: str = ''


def _apply_default_font(font_name: str):
    Label.font_name.defaultvalue     = font_name
    Button.font_name.defaultvalue    = font_name
    TextInput.font_name.defaultvalue = font_name


def register_all_fonts(fonts_dir: str = _FONTS_DIR) -> list:
    global REGISTERED_FONT

    if not os.path.isdir(fonts_dir):
        print(f"[Fonts] mجلد الخطوط غير موجود: {fonts_dir}")
        return []

    fonts = sorted([
        f for f in os.listdir(fonts_dir)
        if f.lower().endswith(('.ttf', '.otf'))
    ])

    if not fonts:
        print(f"[Fonts] لا توجد خطوط في: {fonts_dir}")
        return []

    registered = []
    for file in fonts:
        font_path = os.path.join(fonts_dir, file)
        font_name = os.path.splitext(file)[0]
        try:
            LabelBase.register(name=font_name, fn_regular=font_path)
            registered.append(font_name)
            print(f"[Fonts] OK {font_name}")
        except Exception as e:
            print(f"[Fonts] FAIL {font_name}: {e}")

    if registered:
        REGISTERED_FONT = registered[0]
        _apply_default_font(REGISTERED_FONT)
        print(f"[Fonts] الخط الافتراضي: {REGISTERED_FONT}")

    return registered


register_all_fonts()


# ══════════════════════════════════════════════════════════════════════════════
#  STORAGE
# ══════════════════════════════════════════════════════════════════════════════

APP_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app_data')


def ensure_app_data_dir():
    os.makedirs(APP_DATA_DIR, exist_ok=True)


def get_bot_dir(bot_name: str) -> str:
    safe_name = "".join(c for c in bot_name if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_name = safe_name.replace(' ', '_') or 'bot'
    return os.path.join(APP_DATA_DIR, safe_name)


def save_bot_data(bot_data: dict) -> dict:
    ensure_app_data_dir()

    bot_dir       = get_bot_dir(bot_data.get('name', 'bot'))
    bot_files_dir = os.path.join(bot_dir, 'bot_files')

    os.makedirs(bot_dir,       exist_ok=True)
    os.makedirs(bot_files_dir, exist_ok=True)

    saved_image_path = ''
    original_image   = bot_data.get('image', '')
    if original_image and os.path.isfile(original_image):
        ext  = os.path.splitext(original_image)[1]
        dest = os.path.join(bot_dir, f'avatar{ext}')
        shutil.copy2(original_image, dest)
        saved_image_path = dest

    config = {
        'name':  bot_data.get('name', 'My Bot'),
        'token': bot_data.get('token', ''),
        'image': saved_image_path,
    }

    config_path = os.path.join(bot_files_dir, 'config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    return config


def load_all_bots() -> list:
    ensure_app_data_dir()
    bots = []

    for entry in os.scandir(APP_DATA_DIR):
        if not entry.is_dir():
            continue
        config_path = os.path.join(entry.path, 'bot_files', 'config.json')
        if not os.path.isfile(config_path):
            continue
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            if config.get('image') and not os.path.isfile(config['image']):
                config['image'] = ''
            bots.append(config)
        except Exception as e:
            print(f"[Storage] خطا في تحميل {config_path}: {e}")

    return bots


def bot_exists(bot_name: str) -> bool:
    bot_dir = get_bot_dir(bot_name)
    return os.path.isfile(os.path.join(bot_dir, 'bot_files', 'config.json'))


# ══════════════════════════════════════════════════════════════════════════════
#  THEME
# ══════════════════════════════════════════════════════════════════════════════

THEME = {
    'bg':             '#FFFFFF',
    'card_bg':        '#C7D6FF',
    'card_border':    '#FFFFFF',
    'footer_bg':      '#A3CBFF',
    'popup_bg':       '#FFFFFF',
    'input_bg':       '#818181',
    'input_border':   '#797979',
    'text':           '#000000',
    'text_dim':       '#8A90A8',
    'text_on_accent': '#FFFFFF',
    'accent':         '#1B1F2E',
    'accent_hover':   '#2C3150',
    'success':        '#16A34A',
    'danger':         '#DC2626',
    'icon_bg':        '#8F8F8F',
    'discord':        '#5865F2',
    'github':         '#24292E',
    'title_bcfd':     '#1B1F2E',
}


def _c(key: str):
    return get_color_from_hex(THEME[key])


def _font() -> str:
    return REGISTERED_FONT or Label.font_name.defaultvalue or 'font'


def _draw_card(w, radius=12):
    with w.canvas.before:
        Color(*_c('card_bg'))
        rect   = RoundedRectangle(pos=w.pos, size=w.size, radius=[dp(radius)])
        Color(*_c('card_border'))
        border = Line(
            rounded_rectangle=(w.x, w.y, w.width, w.height, dp(radius)),
            width=1.1,
        )
    w.bind(
        pos =lambda i, v: (
            setattr(rect,   'pos', v),
            setattr(border, 'rounded_rectangle',
                    (v[0], v[1], i.width, i.height, dp(radius))),
        ),
        size=lambda i, v: (
            setattr(rect,   'size', v),
            setattr(border, 'rounded_rectangle',
                    (i.x, i.y, v[0], v[1], dp(radius))),
        ),
    )


def _draw_input(inp):
    with inp.canvas.before:
        Color(*_c('input_bg'))
        inp._bg = RoundedRectangle(pos=inp.pos, size=inp.size, radius=[dp(10)])
        Color(*_c('input_border'))
        inp._bd = Line(
            rounded_rectangle=(inp.x, inp.y, inp.width, inp.height, dp(10)),
            width=1.1,
        )
    inp.bind(
        pos =lambda i, v: (
            setattr(i._bg, 'pos', v),
            setattr(i._bd, 'rounded_rectangle',
                    (v[0], v[1], i.width, i.height, dp(10))),
        ),
        size=lambda i, v: (
            setattr(i._bg, 'size', v),
            setattr(i._bd, 'rounded_rectangle',
                    (i.x, i.y, v[0], v[1], dp(10))),
        ),
    )


# ══════════════════════════════════════════════════════════════════════════════
#  BotCard
# ══════════════════════════════════════════════════════════════════════════════

class BotCard(BoxLayout):

    def __init__(self, bot_data: dict, on_start, on_stop, on_delete,
                 manager=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation     = 'horizontal'
        self.size_hint_y     = None
        self.height          = dp(70)
        self.padding         = [dp(14), dp(10), dp(14), dp(10)]
        self.spacing         = dp(12)
        self.bot_data        = bot_data
        self._running        = False
        self._on_start       = on_start
        self._on_stop        = on_stop
        self._screen_manager = manager
        _draw_card(self, radius=12)

        img_path = bot_data.get('image', '')
        if img_path and os.path.isfile(img_path):
            icon = Image(
                source=img_path,
                size_hint=(None, None),
                size=(dp(42), dp(42)),
                fit_mode='cover',
            )
        else:
            icon = Label(
                text=_t('avatar_none'),
                font_size=dp(11),
                font_name=_font(),
                color=_c('text_dim'),
                size_hint=(None, 1), width=dp(42),
            )
        self.add_widget(icon)

        info = BoxLayout(orientation='vertical', spacing=dp(2))
        self._name_lbl = Label(
            text=bot_data.get('name', 'Bot'),
            font_size=dp(14), bold=True,
            color=_c('text'),
            font_name=_font(),
            halign='left', valign='middle',
        )
        self._name_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        info.add_widget(self._name_lbl)
        self.add_widget(info)

        btns = BoxLayout(orientation='horizontal',
                         size_hint=(None, 1), width=dp(96), spacing=dp(6))

        self._play_btn = Button(
            text='->',
            font_size=dp(16),
            font_name=_font(),
            background_normal='',
            background_color=_c('accent'),
            color=(1, 1, 1, 1),
            size_hint=(None, None), size=(dp(40), dp(40)),
        )
        self._play_btn.bind(on_press=self._go_to_external_main)
        btns.add_widget(self._play_btn)
        self.add_widget(btns)

    def _go_to_external_main(self, _):
        if not self._screen_manager:
            return
        if not self._screen_manager.has_screen('bot_dashboard'):
            return

        bot_name  = self.bot_data.get('name', 'bot')
        safe_name = "".join(
            c for c in bot_name if c.isalnum() or c in (' ', '-', '_')
        ).strip().replace(' ', '_') or 'bot'

        bot_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        'app_data', safe_name, 
        )

        dashboard = self._screen_manager.get_screen('bot_dashboard')
        dashboard.load_bot(bot_dir)
        self._screen_manager.current = 'bot_dashboard'


# ══════════════════════════════════════════════════════════════════════════════
#  CreateBotPopup
# ══════════════════════════════════════════════════════════════════════════════

class CreateBotPopup(Popup):

    def __init__(self, on_create: callable, **kwargs):
        super().__init__(**kwargs)
        self.on_create_cb     = on_create
        self._image_path      = ''
        self.title            = ''
        self.separator_height = 0
        self.size_hint        = (0.86, None)
        self.height           = dp(460)
        self.background       = ''
        self.background_color = (0, 0, 0, 0)

        root = BoxLayout(
            orientation='vertical',
            padding=[dp(24), dp(24), dp(24), dp(24)],
            spacing=dp(12),
        )
        with root.canvas.before:
            Color(*_c('popup_bg'))
            root._bg = RoundedRectangle(pos=root.pos, size=root.size, radius=[dp(18)])
            Color(*_c('card_border'))
            root._bd = Line(
                rounded_rectangle=(root.x, root.y, root.width, root.height, dp(18)),
                width=1.2,
            )
        root.bind(
            pos =lambda i, v: (
                setattr(i._bg, 'pos', v),
                setattr(i._bd, 'rounded_rectangle',
                        (v[0], v[1], i.width, i.height, dp(18))),
            ),
            size=lambda i, v: (
                setattr(i._bg, 'size', v),
                setattr(i._bd, 'rounded_rectangle',
                        (i.x, i.y, v[0], v[1], dp(18))),
            ),
        )

        # ── صورة البوت ───────────────────────────────────────────────
        img_wrap = BoxLayout(size_hint=(1, None), height=dp(86))
        img_wrap.add_widget(Label(size_hint_x=1))

        self._img_btn = Button(
            size_hint=(None, None), size=(dp(80), dp(80)),
            background_normal='', background_color=(0, 0, 0, 0),
        )
        self._img_btn.bind(on_press=self._pick_image)

        with self._img_btn.canvas.before:
            Color(*_c('icon_bg'))
            self._img_circle = Ellipse(pos=self._img_btn.pos, size=self._img_btn.size)
        self._img_btn.bind(
            pos =lambda i, v: setattr(self._img_circle, 'pos', v),
            size=lambda i, v: setattr(self._img_circle, 'size', v),
        )

        self._img_lbl = Label(
            text=_t('image_label'),
            font_size=dp(13),
            font_name=_font(),
            color=_c('text'),
            halign='center', valign='middle', size_hint=(1, 1),
        )
        self._img_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        self._img_btn.add_widget(self._img_lbl)
        self._img_widget = None

        img_wrap.add_widget(self._img_btn)
        img_wrap.add_widget(Label(size_hint_x=1))
        root.add_widget(img_wrap)

        root.add_widget(self._dim(_t('name_label')))
        self._name = self._field(_t('name_hint'), root)

        root.add_widget(self._dim(_t('token_label')))
        self._token = self._field(_t('token_hint'), root, password=True)

        make = Button(
            text=_t('make'),
            size_hint=(1, None), height=dp(46),
            background_normal='', background_color=_c('accent'),
            color=(1, 1, 1, 1), font_size=dp(15), bold=True,
            font_name=_font(),
        )
        make.bind(on_press=self._submit)
        root.add_widget(make)

        self.content = root

    def _pick_image(self, _):
        filechooser.open_file(
            title='Choose Bot Image',
            filters=[('Images', '*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp')],
            on_selection=self._set_image,
        )

    def _set_image(self, selection):
        if not selection:
            return
        path = selection[0]
        if not os.path.isfile(path):
            return
        self._image_path = path
        self._img_btn.clear_widgets()
        img = Image(
            source=path,
            size_hint=(None, None), size=(dp(80), dp(80)),
            fit_mode='contain',
            pos=(self._img_btn.x, self._img_btn.y),
        )
        with img.canvas.before:
            Color(1, 1, 1, 1)
            self._mask = Ellipse(pos=img.pos, size=img.size)
        img.bind(
            pos =lambda i, v: setattr(self._mask,   'pos',  v),
            size=lambda i, v: setattr(self._mask,   'size', v),
        )
        with img.canvas.after:
            Color(0, 0, 0, 1)
            self._border = Line(
                rounded_rectangle=(img.x, img.y, img.width, img.height, dp(40)),
                width=2,
            )
        img.bind(
            pos =lambda i, v: setattr(self._border, 'rounded_rectangle',
                                      (v[0], v[1], i.width, i.height, dp(40))),
            size=lambda i, v: setattr(self._border, 'rounded_rectangle',
                                      (i.x, i.y, v[0], v[1], dp(40))),
        )
        self._img_btn.add_widget(img)
        self._img_widget = img

    def _dim(self, text: str) -> Label:
        lbl = Label(
            text=text, font_size=dp(11), bold=True,
            color=_c('text_dim'),
            font_name=_font(),
            size_hint=(1, None), height=dp(15), halign='left',
        )
        lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        return lbl

    def _field(self, hint: str, parent, password=False) -> TextInput:
        inp = TextInput(
            hint_text=hint,
            hint_text_color=(0, 0, 0, 0.4),
            foreground_color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1),
            cursor_color=(0, 0, 0, 1),
            font_size=dp(14),
            font_name=_font(),
            multiline=False, password=password,
            size_hint=(1, None), height=dp(46),
            padding=[dp(10), dp(5), dp(5), dp(10)],
            halign='left',
        )
        parent.add_widget(inp)
        return inp

    def _submit(self, _):
        name  = self._name.text.strip() or 'My Bot'
        token = self._token.text.strip()
        if not token:
            self._token.hint_text = _t('token_required')
            return
        self.dismiss()
        self.on_create_cb({'name': name, 'token': token, 'image': self._image_path})


# ══════════════════════════════════════════════════════════════════════════════
#  Warning Popup  (بدون ايموجي)
# ══════════════════════════════════════════════════════════════════════════════

def _show_warning(message: str):
    content = BoxLayout(
        orientation='vertical',
        padding=[dp(20), dp(20), dp(20), dp(20)],
        spacing=dp(14),
    )

    with content.canvas.before:
        Color(*get_color_from_hex(THEME['popup_bg']))
        content._bg = RoundedRectangle(pos=content.pos, size=content.size, radius=[dp(16)])
        Color(*get_color_from_hex(THEME['danger']))
        content._bd = Line(
            rounded_rectangle=(content.x, content.y, content.width, content.height, dp(16)),
            width=1.4,
        )
    content.bind(
        pos =lambda i, v: (
            setattr(i._bg, 'pos', v),
            setattr(i._bd, 'rounded_rectangle',
                    (v[0], v[1], i.width, i.height, dp(16))),
        ),
        size=lambda i, v: (
            setattr(i._bg, 'size', v),
            setattr(i._bd, 'rounded_rectangle',
                    (i.x, i.y, v[0], v[1], dp(16))),
        ),
    )

    icon = Label(
        text='!',
        font_size=dp(34), bold=True,
        font_name=_font(),
        size_hint=(1, None), height=dp(44),
        halign='center',
        color=get_color_from_hex(THEME['danger']),
    )
    icon.bind(size=lambda i, v: setattr(i, 'text_size', v))

    msg = Label(
        text=message,
        font_size=dp(13),
        color=get_color_from_hex(THEME['text']),
        font_name=_font(),
        halign='center', valign='middle',
        size_hint=(1, None), height=dp(50),
    )
    msg.bind(size=lambda i, v: setattr(i, 'text_size', v))

    close_btn = Button(
        text=_t('ok'),
        size_hint=(1, None), height=dp(42),
        background_normal='', background_color=get_color_from_hex(THEME['danger']),
        color=(1, 1, 1, 1), font_size=dp(14), bold=True,
        font_name=_font(),
    )

    content.add_widget(icon)
    content.add_widget(msg)
    content.add_widget(close_btn)

    popup = Popup(
        title='', separator_height=0,
        size_hint=(0.78, None), height=dp(220),
        background='', background_color=(0, 0, 0, 0),
        content=content,
    )
    close_btn.bind(on_press=popup.dismiss)
    popup.open()


# ══════════════════════════════════════════════════════════════════════════════
#  MainScreen
# ══════════════════════════════════════════════════════════════════════════════

class MainScreen(Screen):

    def __init__(self, app_instance, manager=None, **kwargs):
        super().__init__(**kwargs)
        self.app_instance    = app_instance
        self._screen_manager = manager
        self.name            = 'main'
        self._build()

    def on_enter(self, *args):
        pass

    def _build(self):
        Window.clearcolor = _c('bg')
        root = FloatLayout()

        # ── Header ───────────────────────────────────────────────────
        header = BoxLayout(
            orientation='horizontal', size_hint=(1, None),
            height=dp(52), pos_hint={'top': 1},
            padding=[dp(18), dp(10), dp(18), dp(10)],
        )
        title_box = BoxLayout(orientation='horizontal',
                              size_hint=(None, 1), width=dp(130))
        lbl_bcfd = Label(
            text='[b]' + _t('main_title') + '[/b]', markup=True,
            font_size=dp(22), color=_c('title_bcfd'),
            font_name=_font(),
            size_hint=(None, 1), width=dp(80),
            halign='left', valign='middle',
        )
        lbl_bcfd.bind(size=lambda i, v: setattr(i, 'text_size', v))
        title_box.add_widget(lbl_bcfd)
        header.add_widget(title_box)
        header.add_widget(Label(size_hint_x=1))
        root.add_widget(header)

        # ── قائمة البوتات ─────────────────────────────────────────────
        scroll = ScrollView(size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
                            do_scroll_x=False)
        self._grid = GridLayout(
            cols=1, spacing=dp(10), size_hint_y=None,
            padding=[dp(16), dp(60), dp(16), dp(74)],
        )
        self._grid.bind(minimum_height=self._grid.setter('height'))
        scroll.add_widget(self._grid)
        root.add_widget(scroll)

        self._empty = Label(
            text=_t('no_bots_hint'),
            font_size=dp(14), color=_c('text_dim'),
            font_name=_font(),
            halign='center',
            size_hint=(None, None), size=(dp(300), dp(40)),
            pos_hint={'center_x': 0.5, 'center_y': 0.52},
        )
        self._empty.bind(size=lambda i, v: setattr(i, 'text_size', v))
        root.add_widget(self._empty)

        # ── Footer ───────────────────────────────────────────────────
        footer = BoxLayout(
            orientation='horizontal', size_hint=(1, None),
            height=dp(62), pos_hint={'x': 0, 'y': 0},
            padding=[dp(14), dp(11), dp(14), dp(11)], spacing=dp(8),
        )
        with footer.canvas.before:
            Color(*_c('footer_bg'))
            fb = RoundedRectangle(pos=footer.pos, size=footer.size, radius=[dp(0)])
            Color(*_c('card_border'))
            fl = Line(points=[], width=1)
        footer.bind(
            pos =lambda i, v: (
                setattr(fb, 'pos', v),
                setattr(fl, 'points',
                        [v[0], v[1] + i.height, v[0] + i.width, v[1] + i.height]),
            ),
            size=lambda i, v: (
                setattr(fb, 'size', v),
                setattr(fl, 'points',
                        [i.x, i.y + v[1], i.x + v[0], i.y + v[1]]),
            ),
        )

        for key, color_key, url in [
            ('discord', 'discord', 'https://discord.gg/JngaJRC6Y9'),
            ('github',  'github',  'https://github.com/Aksjuwu/BCFD-L'),
        ]:
            b = Button(
                text=_t(key),
                size_hint=(None, None), size=(dp(76), dp(38)),
                background_normal='', background_color=_c(color_key),
                color=(1, 1, 1, 1), font_size=dp(12),
                font_name=_font(),
            )
            b.bind(on_press=lambda x, u=url: webbrowser.open(u))
            footer.add_widget(b)

        footer.add_widget(Label(size_hint_x=1))

        add_btn = Button(
            text=_t('new_bot'),
            size_hint=(None, None), size=(dp(96), dp(38)),
            background_normal='', background_color=_c('accent'),
            color=(1, 1, 1, 1), font_size=dp(13), bold=True,
            font_name=_font(),
        )
        add_btn.bind(on_press=lambda x: CreateBotPopup(on_create=self._add_bot).open())
        footer.add_widget(add_btn)

        root.add_widget(footer)
        self.add_widget(root)

        self._load_saved_bots()

    def _load_saved_bots(self):
        for bot_data in load_all_bots():
            self._add_bot_card(bot_data)

    def _add_bot(self, data: dict):
        name = data.get('name', 'My Bot')
        if bot_exists(name):
            _show_warning(_t('name_taken'))
            return
        saved_data = save_bot_data(data)
        self._add_bot_card(saved_data)

    def _add_bot_card(self, bot_data: dict):
        self._empty.opacity = 0
        self._grid.add_widget(BotCard(
            bot_data=bot_data,
            on_start=self._start_bot,
            on_stop=self._stop_bot,
            on_delete=self._remove_bot,
            manager=self._screen_manager,
        ))

    def _remove_bot(self, card):
        self._grid.remove_widget(card)
        if not self._grid.children:
            self._empty.opacity = 1

    def _start_bot(self, data):
        try:
            main_exe.core_bcfd.local_server.start_bot(data.get('token', ''))
        except Exception as e:
            print(f'[BCFD] start: {e}')

    def _stop_bot(self, data):
        try:
            main_exe.core_bcfd.local_server.stop_bot()
        except Exception as e:
            print(f'[BCFD] stop: {e}')


# ══════════════════════════════════════════════════════════════════════════════
#  App
# ══════════════════════════════════════════════════════════════════════════════

class BCFDApp(App):

    def build(self):
        # ── تطبيق الثيم المحفوظ قبل بناء اي شاشة ─────────────────────
        saved_theme = get_current_theme()
        apply_theme_globally(saved_theme)
        Window.clearcolor = _c('bg')

        sm = ScreenManager()

        main_scr = MainScreen(self, manager=sm)
        sm.add_widget(main_scr)

        from main_exe.main import BotDashboardScreen
        dashboard = BotDashboardScreen(main_screen_manager=sm)
        sm.add_widget(dashboard)

        return sm


if __name__ == '__main__':
    BCFDApp().run()