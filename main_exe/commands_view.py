# Copyright (C) 2026 obgwew
# SPDX-License-Identifier: AGPL-3.0-or-later

# -*- coding: utf-8 -*-
# main_exe/commands_view.py . migrated to Flet 0.80+ / v1 API

import cmd
import os
import flet as ft
import re
import threading

from main_exe.theme_engine import ThemeEngine
from main_exe.langs.translations import Translations
from main_exe.settings import get_current_lang

try:
    from main_exe.core_bcfd.FDCore import KNOWN_COMMANDS
except ImportError:
    KNOWN_COMMANDS = set()


# ══════════════════════════════════════════════════════════════════════════════
#  Translation & Language helper
# ══════════════════════════════════════════════════════════════════════════════

def _t(key: str) -> str:
    return Translations.get(key, get_current_lang())

def _ar(text: str) -> str:
    return text

# ══════════════════════════════════════════════════════════════════════════════
#  Theme helper
# ══════════════════════════════════════════════════════════════════════════════

def _c(key: str) -> str:
    return ThemeEngine.hex(key)

# ══════════════════════════════════════════════════════════════════════════════
#  Syntax Highlighting Helper
# ══════════════════════════════════════════════════════════════════════════════

def _get_command_color(word: str) -> str or None:
    if word not in KNOWN_COMMANDS:
        return None
    control_flow = {
        "if", "elif", "else", "endif", "while", "endwhile", "for", "endfor",
        "break", "return", "and", "or", "onlyIf", "onlyAdmin", "log"
    }
    if word in control_flow:
        return "#64008B"
    else:
        return "#22B9FF"


# ══════════════════════════════════════════════════════════════════════════════
#  File utilities
# ══════════════════════════════════════════════════════════════════════════════

def _bot_root_from_dir(bot_dir: str) -> str:
    return os.path.dirname(os.path.abspath(bot_dir))

def _cmds_dir(bot_dir: str) -> str:
    return os.path.join(_bot_root_from_dir(bot_dir), 'bot_commands')

def _get_event_prefixes() -> set[str]:
    try:
        pkg_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'core_bcfd', 'event_FDScripts'
        )
        if not os.path.isdir(pkg_path):
            return {'$onJoined', '$onLeave', '$alwaysReply'}
        prefixes = set()
        for fname in os.listdir(pkg_path):
            if fname.endswith('.py') and not fname.startswith('_'):
                prefixes.add(f'${os.path.splitext(fname)[0]}')
        return prefixes or {'$onJoined', '$onLeave', '$alwaysReply'}
    except Exception:
        return {'$onJoined', '$onLeave', '$alwaysReply'}

def _is_event_prefix(prefix: str) -> bool:
    return prefix.strip() in _get_event_prefixes()

def _events_dir(bot_dir: str) -> str:
    return os.path.join(_bot_root_from_dir(bot_dir), 'bot_events')

def _ensure_events_dir(bot_dir: str) -> str:
    path = _events_dir(bot_dir)
    os.makedirs(path, exist_ok=True)
    return path

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
    results = []

    for folder, is_event in [(_cmds_dir(bot_dir), False), (_events_dir(bot_dir), True)]:
        if not os.path.isdir(folder):
            continue
        try:
            for f in os.listdir(folder):
                if not f.endswith('.py'):
                    continue
                parsed = _parse_cmd_file(os.path.join(folder, f))
                parsed['is_event'] = is_event
                results.append(parsed)
        except Exception:
            pass

    return sorted(results, key=lambda c: c['name'].lower())

def _write_cmd_file(bot_dir: str, name: str, prefix: str,
                    content: str, old_path: str = '') -> str:
    safe     = ''.join(c for c in name if c.isalnum() or c in ('-', '_')).strip() or 'command'

    if _is_event_prefix(prefix):
        dest_dir = _ensure_events_dir(bot_dir)
        folder_label = 'bot_events'
    else:
        dest_dir = _ensure_cmds_dir(bot_dir)
        folder_label = 'bot_commands'

    new_path = os.path.join(dest_dir, f'{safe}.py')

    if old_path and os.path.abspath(old_path) != os.path.abspath(new_path):
        if os.path.isfile(old_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    with open(new_path, 'w', encoding='utf-8') as f:
        f.write(f'#PREFIX:{prefix}\n{content}')

    print(f'[Commands] saved → {new_path}  ({folder_label})')
    return new_path

def _remove_cmd_file(path: str):
    if os.path.isfile(path):
        try:
            os.remove(path)
            print(f'[Commands] deleted → {path}')
        except Exception as e:
            print(f'[Commands] delete error: {e}')


# ══════════════════════════════════════════════════════════════════════════════
#  Style helpers
# ══════════════════════════════════════════════════════════════════════════════

def _btn_style(bg: str, fg: str = '#FFFFFF',
               padding: ft.Padding = None) -> ft.ButtonStyle:
    style = ft.ButtonStyle(bgcolor=bg, color=fg)
    if padding:
        style.padding = padding
    return style

def _border_all(width: float, color: str) -> ft.Border:
    side = ft.BorderSide(width, color)
    return ft.Border(left=side, top=side, right=side, bottom=side)


# ══════════════════════════════════════════════════════════════════════════════
#  Confirm Delete Dialog
# ══════════════════════════════════════════════════════════════════════════════

def _confirm_delete(page: ft.Page, item_name: str, on_confirm: callable):
    def _do(_):
        page.pop_dialog()
        on_confirm()

    def _cancel(_):
        page.pop_dialog()

    formatted_msg = _t('delete_confirm').replace('{item_name}', item_name)

    dlg = ft.AlertDialog(
        modal=True,
        bgcolor=_c('card_bg'),
        shape=ft.RoundedRectangleBorder(radius=16),
        title=ft.Row(
            [
                ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=_c('danger'), size=22),
                ft.Text(_t('delete_q'), weight=ft.FontWeight.BOLD,
                        color=_c('text'), size=16),
            ],
            spacing=8,
        ),
        content=ft.Text(
            _ar(formatted_msg),
            color=_c('text_dim'),
            size=13,
        ),
        actions=[
            ft.TextButton(
                content=ft.Text(_t('cancel'), color=_c('text_dim')),
                on_click=_cancel,
            ),
            ft.FilledButton(
                content=ft.Row(
                    [ft.Icon(ft.Icons.DELETE_FOREVER_ROUNDED, color='#FFFFFF', size=16),
                     ft.Text(_t('delete'), color='#FFFFFF', weight=ft.FontWeight.BOLD)],
                    spacing=6, tight=True,
                ),
                on_click=_do,
                style=ft.ButtonStyle(
                    bgcolor=_c('danger'),
                    color='#FFFFFF',
                    shape=ft.RoundedRectangleBorder(radius=10),
                    padding=ft.Padding(left=14, top=8, right=14, bottom=8),
                ),
            ),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.show_dialog(dlg)

# ══════════════════════════════════════════════════════════════════════════════
#  CommandEditorView
# ══════════════════════════════════════════════════════════════════════════════

class CommandEditorView:

    def __init__(self, page: ft.Page, on_back=None):
        self._page     = page
        self._on_back  = on_back
        self._bot_dir  = ''
        self._cmd_path = ''
        self._debounce_timer = None

        self._name_field = ft.TextField(
            label=_t('name_label'),
            hint_text=_t('name_hint'),
            dense=True,
            border_color=_c('card_border'),
            focused_border_color=_c('accent'),
            label_style=ft.TextStyle(color=_c('text_dim'), size=11),
            text_style=ft.TextStyle(color=_c('text'), size=12),
            cursor_color=_c('accent'),
            bgcolor=_c('card_bg'),
            expand=True,
        )
        self._prefix_field = ft.TextField(
            label=_t('prefix_label'),
            hint_text=_t('prefix_hint'),
            dense=True,
            border_color=_c('card_border'),
            focused_border_color=_c('accent'),
            label_style=ft.TextStyle(color=_c('text_dim'), size=11),
            text_style=ft.TextStyle(color=_c('text'), size=12),
            cursor_color=_c('accent'),
            bgcolor=_c('card_bg'),
            on_change=self._on_prefix_change,
            expand=True,
        )

        self._lines_lbl = ft.Text('0', size=18, weight=ft.FontWeight.BOLD, color=_c('text'))
        self._chars_lbl = ft.Text('0', size=18, weight=ft.FontWeight.BOLD, color=_c('text'))

        self._line_nums = ft.TextField(
            value='1',
            read_only=True,
            multiline=True,
            text_align=ft.TextAlign.RIGHT,
            text_style=ft.TextStyle(color=_c('text_dim'), size=12, font_family="Consolas"),
            bgcolor=_c('card_bg'),
            border=ft.InputBorder.NONE,
            cursor_color='transparent',
            width=36,
            content_padding=ft.Padding(left=2, right=2, top=8, bottom=8),
        )

        self._highlighter = ft.Text(
            size=12,
            font_family="Consolas",
            selectable=False,
        )

        self._code_edit = ft.TextField(
            hint_text=_t('fdscript_hint'),
            multiline=True,
            min_lines=18,
            text_style=ft.TextStyle(color='transparent', size=12, font_family="Consolas"),
            bgcolor='transparent',
            border=ft.InputBorder.NONE,
            cursor_color=_c('accent'),
            content_padding=8,
            expand=True,
            on_change=self._on_code_change,
        )

        self._title_text = ft.Text(
            _ar('New.py'), size=13, weight=ft.FontWeight.BOLD, color=_c('text')
        )
        self._save_btn = ft.FilledButton(
            content=ft.Row(
                [ft.Icon(ft.Icons.SAVE_OUTLINED, color='#FFFFFF'),
                 ft.Text(_t('save'), color='#FFFFFF')],
                spacing=6, tight=True,
            ),
            on_click=self._save,
            style=_btn_style(_c('success')),
        )
        self._dest_indicator = ft.Text(
            _t('dest_cmd'),
            size=10,
            color=_c('text_dim'),
            italic=True,
        )

        ThemeEngine.subscribe(self._on_theme)

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _on_theme(self, data: dict):
        g = lambda k: data.get(k, '#888888')

        for field in (self._name_field, self._prefix_field):
            field.border_color         = g('card_border')
            field.focused_border_color = g('accent')
            field.bgcolor              = g('card_bg')
            field.cursor_color         = g('accent')
            field.label_style          = ft.TextStyle(color=g('text_dim'), size=11)
            field.text_style           = ft.TextStyle(color=g('text'), size=12)

        self._code_edit.cursor_color = g('accent')
        self._line_nums.text_style   = ft.TextStyle(color=g('text_dim'), size=12, font_family="Consolas")
        self._line_nums.bgcolor      = g('card_bg')
        self._lines_lbl.color        = g('text')
        self._chars_lbl.color        = g('text')
        self._title_text.color       = g('text')
        self._save_btn.style         = _btn_style(g('success'))

        self._apply_highlights()

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        header = ft.Container(
            content=ft.Row(
                [
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_ROUNDED,
                        icon_color=_c('text_on_accent'),
                        bgcolor=_c('accent'),
                        on_click=lambda _: self._on_back and self._on_back(),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
                        icon_size=16,
                    ),
                    ft.Text(_t('commands_slash'), size=13, color=_c('text_dim')),
                    self._title_text,
                ],
                spacing=6,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=10, right=10, top=6, bottom=6),
            height=46,
        )

        info_card = ft.Container(
            content=ft.Row(
                [
                    ft.Column(
                        [self._name_field, self._prefix_field, self._dest_indicator],
                        spacing=6,
                        expand=True,
                    ),
                    ft.Column(
                        [
                            _stat_col(_t('total_lines'), self._lines_lbl),
                            _stat_col(_t('total_text'),  self._chars_lbl),
                        ],
                        spacing=4,
                        width=86,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=_c('card_bg'),
            border=_border_all(1, _c('card_border')),
            border_radius=12,
            padding=ft.Padding(left=12, right=12, top=10, bottom=10),
        )

        editor_area = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            self._line_nums,
                            ft.Stack(
                                [
                                    ft.Container(content=self._highlighter, padding=8),
                                    self._code_edit,
                                ],
                                expand=True,
                            )
                        ],
                        spacing=0,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        expand=True,
                    ),
                ],
                spacing=6,
                expand=True,
            ),
            bgcolor=_c('card_bg'),
            border=_border_all(1, _c('card_border')),
            border_radius=10,
            padding=6,
            expand=True,
        )

        return ft.Column(
            [
                header,
                ft.Stack(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(_t('info_command'), size=11, weight=ft.FontWeight.BOLD, color=_c('text_dim')),
                                    info_card,
                                    ft.Text(_t('command_editor'), size=12, weight=ft.FontWeight.BOLD, color=_c('text')),
                                    editor_area,
                                ],
                                spacing=10,
                                scroll=ft.ScrollMode.AUTO,
                                expand=True,
                            ),
                            padding=ft.Padding(left=12, right=12, top=8, bottom=74),
                            expand=True,
                        ),
                        ft.Container(
                            content=self._save_btn,
                            bottom=24,
                            right=24,
                        ),
                    ],
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    # ── event prefix ──────────────────────────────────────────────────────────

    def _on_prefix_change(self, e):
        prefix = (e.control.value or '').strip()
        if _is_event_prefix(prefix):
            self._dest_indicator.value = _t('dest_event')
            self._dest_indicator.color = '#22B9FF'
        else:
            self._dest_indicator.value = _t('dest_cmd')
            self._dest_indicator.color = _c('text_dim')
        self._page.update()

    # ── Highlighting ──────────────────────────────────────────────────────────

    def _apply_highlights(self):
        try:
            text = self._code_edit.value or ''

            if not text:
                self._highlighter.spans = []
                self._highlighter.value = ''
                self._page.update()
                return

            parts       = re.split(r'(\$[a-zA-Z0-9_]+|[\[\];])', text)
            spans       = []
            base_color  = _c('text')
            BRACKET_COLOR   = "#F84B4B"
            SEMICOLON_COLOR = "#FF9500"

            for part in parts:
                if not part:
                    continue

                if part in ('[', ']'):
                    spans.append(ft.TextSpan(
                        part,
                        ft.TextStyle(color=BRACKET_COLOR, weight=ft.FontWeight.BOLD, font_family="Consolas"),
                    ))
                elif part == ';':
                    spans.append(ft.TextSpan(
                        part,
                        ft.TextStyle(color=SEMICOLON_COLOR, weight=ft.FontWeight.BOLD, font_family="Consolas"),
                    ))
                elif part.startswith('$') and len(part) > 1:
                    cmd_name = part[1:]
                    color    = _get_command_color(cmd_name)
                    spans.append(ft.TextSpan(
                        part,
                        ft.TextStyle(
                            color=color if color else base_color,
                            weight=ft.FontWeight.BOLD if color else ft.FontWeight.W_400,
                            font_family="Consolas",
                        ),
                    ))
                else:
                    spans.append(ft.TextSpan(
                        part,
                        ft.TextStyle(color=base_color, font_family="Consolas"),
                    ))

            self._highlighter.spans = spans
            self._page.update()
        except Exception:
            pass

    def _on_code_change(self, e):
        value = e.control.value or ''
        lines = value.count('\n') + 1
        self._line_nums.value = '\n'.join(str(i) for i in range(1, lines + 1))
        self._lines_lbl.value = str(lines)
        self._chars_lbl.value = str(len(value))

        if self._debounce_timer is not None:
            self._debounce_timer.cancel()
            self._debounce_timer = None

        self._apply_highlights()

    # ── Load / Save ───────────────────────────────────────────────────────────

    def load(self, bot_dir: str, cmd_data: dict = None):
        self._bot_dir  = bot_dir
        self._cmd_path = cmd_data.get('path', '') if cmd_data else ''

        if cmd_data:
            self._name_field.value   = cmd_data.get('name', '')
            self._prefix_field.value = cmd_data.get('prefix', '')
            self._code_edit.value    = cmd_data.get('content', '')
            self._title_text.value   = _ar(cmd_data.get('name', 'command') + '.py')
        else:
            self._name_field.value   = ''
            self._prefix_field.value = ''
            self._code_edit.value    = ''
            self._title_text.value   = _ar('New.py')

        content = self._code_edit.value or ''
        lines   = content.count('\n') + 1
        self._line_nums.value = '\n'.join(str(i) for i in range(1, lines + 1))
        self._lines_lbl.value = str(lines)
        self._chars_lbl.value = str(len(content))

        self._apply_highlights()

    def _save(self, _):
        name    = (self._name_field.value or '').strip()
        prefix  = (self._prefix_field.value or '').strip()
        content = self._code_edit.value or ''

        if not name:
            self._name_field.error_text = _t('name_required')
            self._page.update()
            return

        self._name_field.error_text = None
        self._cmd_path              = _write_cmd_file(
            self._bot_dir, name, prefix, content, self._cmd_path
        )
        self._title_text.value = _ar(name + '.py')
        self._page.update()

# ══════════════════════════════════════════════════════════════════════════════
#  CommandsListView
# ══════════════════════════════════════════════════════════════════════════════

class CommandsListView:

    def __init__(self, page: ft.Page, on_open=None):
        self._page     = page
        self._on_open  = on_open
        self._bot_dir  = ''
        self._all_cmds = []

        self._search_field = ft.TextField(
            hint_text=_t('search'),
            height=40,
            width=180,
            content_padding=ft.Padding(left=10, right=10, top=0, bottom=0),
            bgcolor=_c('card_bg'),
            border_color=_c('card_border'),
            border_radius=8,
            on_change=self._on_search,
        )
        self._list_col = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

        ThemeEngine.subscribe(self._on_theme)

    # ── Theme ─────────────────────────────────────────────────────────────────

    def _on_theme(self, data: dict):
        g = lambda k: data.get(k, '#888888')
        self._search_field.border_color         = g('card_border')
        self._search_field.focused_border_color = g('accent')
        self._search_field.bgcolor              = g('card_bg')
        self._search_field.cursor_color         = g('accent')
        if self._bot_dir:
            self._render(self._all_cmds)
        self._page.update()

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self) -> ft.Control:
        header = ft.Container(
            content=ft.Row(
                [
                    ft.Text(_t('commands'), size=15,
                            weight=ft.FontWeight.BOLD, color=_c('text')),
                    self._search_field,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=12, right=12, top=6, bottom=6),
            height=46,
        )

        fab = ft.FloatingActionButton(
            icon=ft.Icons.ADD,
            bgcolor=_c('accent'),
            foreground_color=_c('text_on_accent'),
            on_click=lambda _: self._on_open and self._on_open(None),
            mini=True,
        )

        return ft.Column(
            [
                header,
                ft.Container(
                    content=ft.Stack(
                        [
                            ft.Container(
                                content=self._list_col,
                                padding=ft.Padding(left=12, right=12, top=8, bottom=70),
                                expand=True,
                            ),
                            ft.Container(
                                content=fab,
                                bottom=14,
                                right=14,
                            ),
                        ],
                        expand=True,
                    ),
                    expand=True,
                ),
            ],
            spacing=0,
            expand=True,
        )

    # ── List logic ────────────────────────────────────────────────────────────

    def load(self, bot_dir: str):
        self._bot_dir  = bot_dir
        self._all_cmds = _list_cmd_files(bot_dir)
        self._render(self._all_cmds)

    def _on_search(self, e):
        q        = (e.control.value or '').strip().lower()
        filtered = self._all_cmds if not q else [
            c for c in self._all_cmds
            if q in c['name'].lower() or q in c['prefix'].lower()
        ]
        self._render(filtered)

    def _render(self, cmds: list):
        self._list_col.controls.clear()
        if not cmds:
            self._list_col.controls.append(
                ft.Container(
                    content=ft.Text(
                        _t('no_cmds_hint'),
                        size=13, color=_c('text_dim'),
                        text_align=ft.TextAlign.CENTER,
                    ),
                    alignment=ft.Alignment(0, 0),
                    height=120,
                )
            )
        else:
            for idx, cmd in enumerate(cmds, start=1):
                self._list_col.controls.append(self._cmd_row(idx, cmd))
        self._page.update()

    def _cmd_row(self, num: int, cmd: dict) -> ft.Control:
        is_event = cmd.get('is_event', False)

        name_row = ft.Row(
            [
                ft.Text(_ar(cmd['name']), size=12,
                        weight=ft.FontWeight.BOLD,
                        color=_c('text')),
                ft.Container(
                    content=ft.Text(_t('dest_event'), size=9, color='#FFFFFF'),
                    bgcolor='#22B9FF',
                    border_radius=4,
                    padding=ft.Padding(left=5, right=5, top=1, bottom=1),
                    visible=is_event,
                ),
            ],
            spacing=5,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        return ft.Row(
            [
                ft.Text(
                    str(num), size=17, weight=ft.FontWeight.BOLD,
                    color=_c('text_dim'), width=24,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    name_row,
                                    ft.Text(_ar(cmd['prefix'] or '—'), size=11,
                                            color=_c('text_dim')),
                                ],
                                spacing=2,
                                expand=True,
                            ),
                            ft.FilledButton(
                                content=ft.Text(_t('edit'), color=_c('text_on_accent')),
                                on_click=lambda _, c=cmd: (
                                    self._on_open and self._on_open(c)
                                ),
                                style=_btn_style(
                                    _c('accent'),
                                    _c('text_on_accent'),
                                    ft.Padding(left=10, right=10, top=4, bottom=4),
                                ),
                            ),
                            ft.FilledButton(
                                content=ft.Text(_t('del'), color='#FFFFFF'),
                                on_click=lambda _, c=cmd: self._ask_delete(c),
                                style=_btn_style(
                                    _c('danger'),
                                    '#FFFFFF',
                                    ft.Padding(left=8, right=8, top=4, bottom=4),
                                ),
                            ),
                        ],
                        spacing=6,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=_c('card_bg'),
                    border=_border_all(1, '#22B9FF' if is_event else _c('card_border')),
                    border_radius=10,
                    padding=ft.Padding(left=10, right=10, top=8, bottom=8),
                    expand=True,
                ),
            ],
            spacing=6,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def _ask_delete(self, cmd: dict):
        _confirm_delete(
            self._page,
            item_name=cmd.get('name', 'command'),
            on_confirm=lambda: self._do_delete(cmd),
        )

    def _do_delete(self, cmd: dict):
        _remove_cmd_file(cmd.get('path', ''))
        self.load(self._bot_dir)


# ══════════════════════════════════════════════════════════════════════════════
#  BotCommandsTab
# ══════════════════════════════════════════════════════════════════════════════

class BotCommandsTab:
    def __init__(self, page: ft.Page):
        self._page        = page
        self._bot_dir     = ''
        self._list_view   = CommandsListView(page, on_open=self._open_editor)
        self._editor_view = CommandEditorView(page, on_back=self._close_editor)
        self._container   = ft.Container(expand=True)

    def build(self) -> ft.Control:
        self._container.content = self._list_view.build()
        return self._container

    def load_bot(self, bot_dir: str):
        self._bot_dir = bot_dir
        self._list_view.load(bot_dir)
        self._container.content = self._list_view.build()
        self._page.update()

    def _open_editor(self, cmd_data=None):
        self._editor_view.load(self._bot_dir, cmd_data)
        self._container.content = self._editor_view.build()
        self._page.update()

    def _close_editor(self):
        self._list_view.load(self._bot_dir)
        self._container.content = self._list_view.build()
        self._page.update()


# ══════════════════════════════════════════════════════════════════════════════
#  Shared widget helpers
# ══════════════════════════════════════════════════════════════════════════════

def _stat_col(heading: str, value_ctrl: ft.Text) -> ft.Column:
    return ft.Column(
        [
            ft.Text(heading, size=9, weight=ft.FontWeight.BOLD, color=_c('text_dim')),
            value_ctrl,
        ],
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )