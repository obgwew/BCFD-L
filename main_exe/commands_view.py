# -*- coding: utf-8 -*-
# main_exe/commands_view.py

import os

from kivy.uix.boxlayout    import BoxLayout
from kivy.uix.floatlayout  import FloatLayout
from kivy.uix.scrollview   import ScrollView
from kivy.uix.label        import Label
from kivy.uix.button       import Button
from kivy.uix.textinput    import TextInput
from kivy.uix.widget       import Widget
from kivy.utils            import get_color_from_hex
from kivy.metrics          import dp
from kivy.graphics         import Color, RoundedRectangle, Line

from main_exe.theme_engine import ThemeEngine

# ══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _c(key: str):
    return ThemeEngine.color(key)

def _font() -> str:
    return Label.font_name.defaultvalue or 'Roboto'

def _make_card(widget, radius: int = 10):
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
#  File utilities
# ══════════════════════════════════════════════════════════════════════════════

def _bot_root_from_dir(bot_dir: str) -> str:
    return os.path.dirname(os.path.abspath(bot_dir))


def _cmds_dir(bot_dir: str) -> str:
    return os.path.join(_bot_root_from_dir(bot_dir), 'bot_commands')


def _ensure_cmds_dir(bot_dir: str) -> str:
    path = _cmds_dir(bot_dir)
    os.makedirs(path, exist_ok=True)
    return path


def _parse_cmd_file(path: str) -> dict:
    name = os.path.splitext(os.path.basename(path))[0]
    try:
        with open(path, 'r', encoding='utf-8') as f:
            raw = f.read()
    except Exception:
        return {'name': name, 'prefix': '', 'content': '', 'path': path}

    prefix  = ''
    content = raw
    if raw.startswith('#PREFIX:'):
        nl      = raw.find('\n')
        prefix  = raw[8:nl].strip() if nl != -1 else raw[8:].strip()
        content = raw[nl + 1:] if nl != -1 else ''

    return {'name': name, 'prefix': prefix, 'content': content, 'path': path}


def _list_cmd_files(bot_dir: str) -> list:
    d = _cmds_dir(bot_dir)
    if not os.path.isdir(d):
        return []
    try:
        entries = [
            _parse_cmd_file(os.path.join(d, f))
            for f in os.listdir(d) if f.endswith('.py')
        ]
        return sorted(entries, key=lambda c: c['name'].lower())
    except Exception:
        return []


def _write_cmd_file(bot_dir: str, name: str, prefix: str,
                    content: str, old_path: str = '') -> str:
    safe     = ''.join(c for c in name if c.isalnum() or c in ('-', '_')).strip() or 'command'
    new_path = os.path.join(_cmds_dir(bot_dir), f'{safe}.py')

    if old_path and os.path.abspath(old_path) != os.path.abspath(new_path):
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    _ensure_cmds_dir(bot_dir)

    with open(new_path, 'w', encoding='utf-8') as f:
        f.write(f'#PREFIX:{prefix}\n{content}')

    print(f'[Commands] saved → {new_path}')
    return new_path


def _remove_cmd_file(path: str):
    if os.path.isfile(path):
        try:
            os.remove(path)
            print(f'[Commands] deleted → {path}')
        except Exception as e:
            print(f'[Commands] delete error: {e}')


# ══════════════════════════════════════════════════════════════════════════════
#  CommandEditorView
# ══════════════════════════════════════════════════════════════════════════════

_EDITOR_H = dp(340)


class CommandEditorView(BoxLayout):

    def __init__(self, on_back=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self._on_back    = on_back
        self._bot_dir    = ''
        self._cmd_path   = ''
        self._build()
        ThemeEngine.subscribe(self._on_theme)

    # ── Theme callback ────────────────────────────────────────────────────────

    def _on_theme(self, data: dict):
        c = lambda k: get_color_from_hex(data.get(k, '#888888'))

        # زر الرجوع
        self._back_btn.background_color = c('accent')

        # عناوين الهيدر
        self._section_lbl.color = c('text_dim')
        self._title_lbl.color   = c('text')

        # info card labels
        self._info_lbl.color = c('text_dim')
        for lh in self._input_labels:
            lh.color = c('text_dim')
        for vl in self._stat_labels:
            vl.color = c('text')
        for hl in self._stat_headings:
            hl.color = c('text_dim')

        # cmd section label
        self._cmd_section_lbl.color = c('text')

        # حقول الإدخال (name, prefix)
        for inp in self._info_inputs:
            inp.background_color = c('card_bg')
            inp.foreground_color = c('text')
            inp.cursor_color     = c('accent')

        # محرر الكود
        self._code_edit.background_color = c('card_bg')
        self._code_edit.foreground_color = c('text')
        self._code_edit.cursor_color     = c('accent')

        # أرقام الأسطر
        self._line_nums.background_color = c('nav_bg')
        self._line_nums.foreground_color = c('text_dim')

        # خلفية حاوية المحرر
        self._ed_bg_color.rgba = list(c('card_bg'))
        self._ed_bd_color.rgba = list(c('card_border'))

        # شريط التمرير
        self._inner_sv.bar_color = c('accent')

        # زر الحفظ
        self._save_btn.background_color = c('success')

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        # ── Header ────────────────────────────────────────────────────
        hdr = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(46),
            padding=[dp(10), dp(6), dp(10), dp(6)],
            spacing=dp(8),
        )
        self._back_btn = Button(
            text='<',
            size_hint=(None, None), size=(dp(36), dp(34)),
            background_normal='', background_color=_c('accent'),
            color=(1, 1, 1, 1), font_size=dp(14), bold=True,
            font_name=_font(),
        )
        self._back_btn.bind(on_press=self._go_back)
        hdr.add_widget(self._back_btn)

        title_box = BoxLayout(orientation='horizontal', size_hint=(1, 1), spacing=dp(2))
        self._section_lbl = Label(
            text="Command's /",
            font_size=dp(13), color=_c('text_dim'), font_name=_font(),
            halign='left', valign='middle',
            size_hint=(None, 1), width=dp(88),
        )
        self._section_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        self._title_lbl = Label(
            text='New.py',
            font_size=dp(13), bold=True,
            color=_c('text'), font_name=_font(),
            halign='left', valign='middle',
            size_hint=(1, 1),
        )
        self._title_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        title_box.add_widget(self._section_lbl)
        title_box.add_widget(self._title_lbl)
        hdr.add_widget(title_box)
        self.add_widget(hdr)

        # ── Body ──────────────────────────────────────────────────────
        outer_scroll = ScrollView(do_scroll_x=False, size_hint=(1, 1))
        body = BoxLayout(
            orientation='vertical', size_hint_y=None,
            spacing=dp(10),
            padding=[dp(12), dp(8), dp(12), dp(16)],
        )
        body.bind(minimum_height=body.setter('height'))

        self._info_lbl = Label(
            text='Info Command',
            font_size=dp(11), bold=True, color=_c('text_dim'), font_name=_font(),
            halign='left', valign='middle',
            size_hint=(1, None), height=dp(18),
        )
        self._info_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        body.add_widget(self._info_lbl)

        info_card = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(108),
            padding=[dp(12), dp(10), dp(12), dp(10)],
            spacing=dp(10),
        )
        _make_card(info_card, radius=12)

        # ── حقول Name و Prefix ───────────────────────────────────────
        self._input_labels  = []
        self._info_inputs   = []

        left = BoxLayout(orientation='vertical', spacing=dp(6), size_hint=(1, 1))
        for attr, lbl_txt, hint in [
            ('_name_inp',   'Name',   'cmd_name'),
            ('_prefix_inp', 'Prefix', '!command'),
        ]:
            row = BoxLayout(orientation='vertical', spacing=dp(2),
                            size_hint=(1, None), height=dp(44))
            lh = Label(
                text=lbl_txt, font_size=dp(9), bold=True,
                color=_c('text_dim'), font_name=_font(),
                size_hint=(1, None), height=dp(12),
                halign='left', valign='middle',
            )
            lh.bind(size=lambda i, v: setattr(i, 'text_size', v))
            self._input_labels.append(lh)

            inp = TextInput(
                hint_text=hint, multiline=False,
                font_size=dp(12), font_name=_font(),
                background_color=_c('card_bg'),
                foreground_color=_c('text'),
                cursor_color=_c('accent'),
                size_hint=(1, None), height=dp(30),
                padding=[dp(8), dp(4), dp(8), dp(4)],
            )
            self._info_inputs.append(inp)
            setattr(self, attr, inp)
            row.add_widget(lh)
            row.add_widget(inp)
            left.add_widget(row)
        info_card.add_widget(left)

        # ── إحصائيات Lines / Chars ───────────────────────────────────
        self._stat_labels   = []
        self._stat_headings = []

        right = BoxLayout(orientation='vertical', spacing=dp(4),
                          size_hint=(None, 1), width=dp(86))
        for attr, heading in [('_lines_lbl', 'Total Lines'), ('_chars_lbl', 'Total Text')]:
            col = BoxLayout(orientation='vertical', spacing=dp(0),
                            size_hint=(1, None), height=dp(44))
            h_lbl = Label(
                text=heading, font_size=dp(9), bold=True,
                color=_c('text_dim'), font_name=_font(),
                size_hint=(1, None), height=dp(14),
                halign='center', valign='middle',
            )
            h_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
            self._stat_headings.append(h_lbl)

            v_lbl = Label(
                text='0', font_size=dp(18), bold=True,
                color=_c('text'), font_name=_font(),
                size_hint=(1, None), height=dp(28),
                halign='center', valign='middle',
            )
            v_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
            self._stat_labels.append(v_lbl)
            setattr(self, attr, v_lbl)
            col.add_widget(h_lbl)
            col.add_widget(v_lbl)
            right.add_widget(col)
        info_card.add_widget(right)
        body.add_widget(info_card)

        self._cmd_section_lbl = Label(
            text='Command',
            font_size=dp(12), bold=True, color=_c('text'), font_name=_font(),
            size_hint=(1, None), height=dp(20),
            halign='left', valign='middle',
        )
        self._cmd_section_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        body.add_widget(self._cmd_section_lbl)

        # ── حاوية المحرر ──────────────────────────────────────────────
        editor_wrap = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=_EDITOR_H + dp(8),
        )
        with editor_wrap.canvas.before:
            self._ed_bg_color = Color(*_c('card_bg'))
            self._ed_bg       = RoundedRectangle(
                pos=editor_wrap.pos, size=editor_wrap.size, radius=[dp(10)])
            self._ed_bd_color = Color(*_c('card_border'))
            self._ed_bd       = Line(
                rounded_rectangle=(
                    editor_wrap.x, editor_wrap.y,
                    editor_wrap.width, editor_wrap.height, dp(10)),
                width=1.1,
            )
        editor_wrap.bind(
            pos=lambda i, v: (
                setattr(self._ed_bg, 'pos', v),
                setattr(self._ed_bd, 'rounded_rectangle',
                        (v[0], v[1], i.width, i.height, dp(10))),
            ),
            size=lambda i, v: (
                setattr(self._ed_bg, 'size', v),
                setattr(self._ed_bd, 'rounded_rectangle',
                        (i.x, i.y, v[0], v[1], dp(10))),
            ),
        )

        self._inner_sv = ScrollView(
            do_scroll_x=False, do_scroll_y=True,
            size_hint=(1, None), height=_EDITOR_H,
            scroll_type=['bars', 'content'],
            bar_width=dp(6),
            bar_color=_c('accent'),
            bar_inactive_color=[.4, .4, .4, .3],
            always_overscroll=False,
        )
        code_row = BoxLayout(orientation='horizontal', size_hint=(1, None))
        code_row.bind(minimum_height=code_row.setter('height'))

        self._line_nums = TextInput(
            text='1', readonly=True, multiline=True,
            size_hint=(None, None), width=dp(36), height=_EDITOR_H,
            font_size=dp(11), font_name=_font(),
            background_color=_c('nav_bg'),
            foreground_color=_c('text_dim'),
            halign='right',
            padding=[dp(2), dp(8), dp(4), dp(8)],
            cursor_color=(0, 0, 0, 0),
        )
        self._code_edit = TextInput(
            hint_text='# Python code here',
            multiline=True,
            size_hint=(1, None), height=_EDITOR_H,
            font_size=dp(12), font_name=_font(),
            background_color=_c('card_bg'),
            foreground_color=_c('text'),
            cursor_color=_c('accent'),
            padding=[dp(8), dp(8), dp(8), dp(8)],
            do_wrap=False,
        )
        self._code_edit.bind(
            minimum_height=self._sync_editor_height,
            text=self._on_code_change,
        )
        code_row.add_widget(self._line_nums)
        code_row.add_widget(self._code_edit)
        self._inner_sv.add_widget(code_row)
        editor_wrap.add_widget(self._inner_sv)

        save_row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(36),
            padding=[dp(6), dp(2), dp(6), dp(2)],
        )
        save_row.add_widget(Widget(size_hint_x=1))
        self._save_btn = Button(
            text='Save',
            size_hint=(None, None), size=(dp(68), dp(30)),
            background_normal='', background_color=_c('success'),
            color=(1, 1, 1, 1), font_size=dp(12), bold=True,
            font_name=_font(),
        )
        self._save_btn.bind(on_press=self._save)
        save_row.add_widget(self._save_btn)
        editor_wrap.add_widget(save_row)

        body.add_widget(editor_wrap)
        outer_scroll.add_widget(body)
        self.add_widget(outer_scroll)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sync_editor_height(self, instance, min_height):
        new_h = max(min_height, _EDITOR_H)
        if abs(self._code_edit.height - new_h) > 1:
            self._code_edit.height = new_h
            self._line_nums.height = new_h

    def _on_code_change(self, instance, value):
        lines = value.count('\n') + 1
        self._line_nums.text = '\n'.join(str(i) for i in range(1, lines + 1))
        self._lines_lbl.text = str(lines)
        self._chars_lbl.text = str(len(value))

    def load(self, bot_dir: str, cmd_data: dict = None):
        self._bot_dir  = bot_dir
        self._cmd_path = cmd_data.get('path', '') if cmd_data else ''
        if cmd_data:
            self._name_inp.text   = cmd_data.get('name', '')
            self._prefix_inp.text = cmd_data.get('prefix', '')
            self._code_edit.text  = cmd_data.get('content', '')
            self._title_lbl.text  = cmd_data.get('name', 'command') + '.py'
        else:
            self._name_inp.text   = ''
            self._prefix_inp.text = ''
            self._code_edit.text  = ''
            self._title_lbl.text  = 'New.py'

    def _go_back(self, *_):
        if callable(self._on_back):
            self._on_back()

    def _save(self, _):
        name    = self._name_inp.text.strip()
        prefix  = self._prefix_inp.text.strip()
        content = self._code_edit.text

        if not name:
            self._name_inp.hint_text = 'Name is required'
            return

        self._cmd_path       = _write_cmd_file(
            self._bot_dir, name, prefix, content, self._cmd_path
        )
        self._title_lbl.text = name + '.py'


# ══════════════════════════════════════════════════════════════════════════════
#  CommandsListView
# ══════════════════════════════════════════════════════════════════════════════

class CommandsListView(BoxLayout):

    def __init__(self, on_open=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self._on_open    = on_open
        self._bot_dir    = ''
        self._all_cmds   = []
        self._build()
        ThemeEngine.subscribe(self._on_theme)

    # ── Theme callback ────────────────────────────────────────────────────────

    def _on_theme(self, data: dict):
        c = lambda k: get_color_from_hex(data.get(k, '#888888'))

        self._title_lbl.color             = c('text')
        self._search_inp.background_color = c('card_bg')
        self._search_inp.foreground_color = c('text')
        self._search_inp.cursor_color     = c('accent')

        # تحديث لون FAB عبر كائن Color المحفوظ
        self._fab_color.rgba = list(c('accent'))

        # إعادة رسم القائمة بألوان الثيم الجديد
        if self._bot_dir:
            self._render(self._all_cmds)

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build(self):
        hdr = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(46),
            padding=[dp(12), dp(6), dp(12), dp(6)],
            spacing=dp(8),
        )
        self._title_lbl = Label(
            text="Command's",
            font_size=dp(15), bold=True,
            color=_c('text'), font_name=_font(),
            halign='left', valign='middle',
            size_hint=(None, 1), width=dp(108),
        )
        self._title_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        hdr.add_widget(self._title_lbl)

        self._search_inp = TextInput(
            hint_text='Search',
            multiline=False, font_size=dp(12), font_name=_font(),
            background_color=_c('card_bg'),
            foreground_color=_c('text'),
            cursor_color=_c('accent'),
            size_hint=(1, None), height=dp(34),
            padding=[dp(8), dp(6), dp(8), dp(6)],
        )
        self._search_inp.bind(text=self._on_search)
        hdr.add_widget(self._search_inp)
        self.add_widget(hdr)

        content = FloatLayout(size_hint=(1, 1))
        scroll = ScrollView(
            do_scroll_x=False, size_hint=(1, 1),
            pos_hint={'x': 0, 'y': 0},
        )
        self._grid = BoxLayout(
            orientation='vertical', size_hint_y=None,
            spacing=dp(10),
            padding=[dp(12), dp(8), dp(12), dp(70)],
        )
        self._grid.bind(minimum_height=self._grid.setter('height'))
        scroll.add_widget(self._grid)
        content.add_widget(scroll)

        fab = Button(
            text='+',
            size_hint=(None, None), size=(dp(60), dp(40)),
            pos_hint={'right': 0.96, 'y': 0.02},
            background_normal='', background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1), font_size=dp(22), bold=True,
            font_name=_font(),
        )
        with fab.canvas.before:
            # نحفظ Color كـ self لتحديثه لاحقاً في _on_theme
            self._fab_color = Color(*_c('accent'))
            self._fab_rect  = RoundedRectangle(pos=fab.pos, size=fab.size, radius=[dp(20)])
        fab.bind(
            pos=lambda i, v: setattr(self._fab_rect, 'pos', v),
            size=lambda i, v: setattr(self._fab_rect, 'size', v),
        )
        fab.bind(on_press=lambda _: self._on_open and self._on_open(None))
        content.add_widget(fab)
        self.add_widget(content)

    # ── List logic ────────────────────────────────────────────────────────────

    def load(self, bot_dir: str):
        self._bot_dir  = bot_dir
        self._all_cmds = _list_cmd_files(bot_dir)
        self._render(self._all_cmds)

    def _on_search(self, _, value: str):
        q = (value or '').strip().lower()
        filtered = self._all_cmds if not q else [
            c for c in self._all_cmds
            if q in c['name'].lower() or q in c['prefix'].lower()
        ]
        self._render(filtered)

    def _render(self, cmds: list):
        self._grid.clear_widgets()
        if not cmds:
            empty = Label(
                text='No commands yet.  Tap + to create one.',
                font_size=dp(13), color=_c('text_dim'), font_name=_font(),
                halign='center', valign='middle',
                size_hint=(1, None), height=dp(120),
            )
            empty.bind(size=lambda i, v: setattr(i, 'text_size', v))
            self._grid.add_widget(empty)
            return
        for idx, cmd in enumerate(cmds, start=1):
            self._grid.add_widget(self._cmd_row(idx, cmd))

    def _cmd_row(self, num: int, cmd: dict) -> BoxLayout:
        row = BoxLayout(
            orientation='horizontal',
            size_hint=(1, None), height=dp(52),
            spacing=dp(6),
        )
        num_lbl = Label(
            text=str(num),
            font_size=dp(17), bold=True,
            color=_c('text_dim'), font_name=_font(),
            size_hint=(None, 1), width=dp(24),
            halign='center', valign='middle',
        )
        num_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        row.add_widget(num_lbl)

        card = BoxLayout(
            orientation='horizontal', size_hint=(1, 1),
            padding=[dp(10), dp(8), dp(8), dp(8)], spacing=dp(6),
        )
        _make_card(card, radius=10)

        info_lbl = Label(
            text=f"NameCMD: {cmd['name']}    Prefix: {cmd['prefix'] or '—'}",
            font_size=dp(11), color=_c('text'), font_name=_font(),
            halign='left', valign='middle', size_hint=(1, 1),
        )
        info_lbl.bind(size=lambda i, v: setattr(i, 'text_size', v))
        card.add_widget(info_lbl)

        edit_btn = Button(
            text='Edit',
            size_hint=(None, None), size=(dp(42), dp(32)),
            background_normal='', background_color=_c('accent'),
            color=(1, 1, 1, 1), font_size=dp(11), bold=True,
            font_name=_font(),
        )
        edit_btn.bind(on_press=lambda _, c=cmd: self._on_open and self._on_open(c))
        card.add_widget(edit_btn)

        del_btn = Button(
            text='Del',
            size_hint=(None, None), size=(dp(36), dp(32)),
            background_normal='', background_color=_c('danger'),
            color=(1, 1, 1, 1), font_size=dp(11), bold=True,
            font_name=_font(),
        )
        del_btn.bind(on_press=lambda _, c=cmd: self._delete_cmd(c))
        card.add_widget(del_btn)

        row.add_widget(card)
        return row

    def _delete_cmd(self, cmd: dict):
        _remove_cmd_file(cmd.get('path', ''))
        self.load(self._bot_dir)


# ══════════════════════════════════════════════════════════════════════════════
#  BotCommandsTab
# ══════════════════════════════════════════════════════════════════════════════

class BotCommandsTab(BoxLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation  = 'vertical'
        self._bot_dir     = ''
        self._list_view   = CommandsListView(on_open=self._open_editor)
        self._editor_view = CommandEditorView(on_back=self._close_editor)
        self.add_widget(self._list_view)

    def load_bot(self, bot_dir: str):
        self._bot_dir = bot_dir
        self._list_view.load(bot_dir)
        if self._editor_view.parent:
            self._close_editor()

    def _open_editor(self, cmd_data=None):
        self._editor_view.load(self._bot_dir, cmd_data)
        self.clear_widgets()
        self.add_widget(self._editor_view)

    def _close_editor(self):
        self._list_view.load(self._bot_dir)
        self.clear_widgets()
        self.add_widget(self._list_view)