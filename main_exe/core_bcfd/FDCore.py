# FDCore.py — Shared Infrastructure for FDScript Gen 2
# Imported by both FDScript.py and every cmds_FDScripts/cmd_*.py
# ─────────────────────────────────────────────────────────────

import asyncio
import discord
import io
import json
import os
import re
import random
import time

# ─────────────────────────────────────────────
# Persistent storage globals
# ─────────────────────────────────────────────

_VARS_DIR: str = ''
_BOT_START_TIME: float = 0.0
_inline_resolver = None  # registered by FDScript to avoid circular imports
_cooldowns: dict = {}


def set_bot_start_time(t: float):
    global _BOT_START_TIME
    _BOT_START_TIME = t


def set_vars_dir(path: str):
    global _VARS_DIR
    _VARS_DIR = path


def register_inline_resolver(fn):
    """Called once by FDScript at import time. fn(cmd_name, args, ctx) -> str | None"""
    global _inline_resolver
    _inline_resolver = fn


def _load_data() -> dict:
    if not _VARS_DIR or not os.path.isdir(_VARS_DIR):
        return {}
    result = {}
    for fname in os.listdir(_VARS_DIR):
        if not fname.endswith('.json'):
            continue
        try:
            with open(os.path.join(_VARS_DIR, fname), 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict) and 'name' in data:
                result[data['name']] = data.get('value', '')
        except Exception:
            pass
    return result


def _save_data(data: dict):
    if not _VARS_DIR:
        return
    os.makedirs(_VARS_DIR, exist_ok=True)
    for name, value in data.items():
        safe = ''.join(c for c in name if c.isalnum() or c in ('-', '_')).strip() or 'var'
        path = os.path.join(_VARS_DIR, f'{safe}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'name': name, 'value': str(value)}, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# Reserved command names
# ─────────────────────────────────────────────

KNOWN_COMMANDS: set[str] = {
    # a
    "addBotReactions", "addTimestamp", "addUserReactions", "and", "authorID", "authorName",
    # b
    "ban", "botID", "botName", "break",
    # c
    "channelID", "channelName", "clear", "clientTyping", "color", "cooldown",
    # d
    "deletecommand", "description", "div", "dm",
    # e
    "elif", "else", "endfor", "endif", "endwhile",
    # f
    "footer", "for",
    # g
    "getBotInvent", "getVar", "guildID", "guildName",
    # i
    "if", "image",
    # k
    "kick",
    # l
    "log",
    # m
    "membersCount", "mention", "message", "messageID", "mod", "mul",
    # o
    "onlyAdmin", "onlyIf", "or",
    # p
    "ping",
    # r
    "randomint", "randomstr", "randomUserID", "replaceText", "reply", "replyIn", "return",
    "returnGetReactions", "returnGuildChannelsID", "returnGuildRolesID", "returnGuildUsersID",
    # s
    "sendEmbedMessage", "sendMessage", "setVar", "slowmode", "strictArgs", "sub", "sum",
    # t
    "timeout", "title",
    # u
    "unban", "untimeout", "uptime",
    # v
    "var",
    # w
    "wait", "while"
}


def get_reserved_names() -> set[str]:
    return KNOWN_COMMANDS


# ─────────────────────────────────────────────
# Error classes
# ─────────────────────────────────────────────

class StopExecution(Exception):
    pass


class _FDError(Exception):
    _category: str = "Error"
    _icon: str = "❌"

    def __init__(self, message: str):
        super().__init__(message)
        self.msg = message


class FDSyntaxError(_FDError):
    _category = "Syntax Error"
    _icon = "🔴"


class FDLogicError(_FDError):
    _category = "Logic Error"
    _icon = "🟠"


class FDRuntimeError(_FDError):
    _category = "Runtime Error"
    _icon = "🟡"


class FDEnvironmentError(_FDError):
    _category = "Environment Error"
    _icon = "🔵"

class FDAbortScript(Exception):
    pass

async def _send_error(ch, error) -> None:
    if ch is not None:
        try:
            await ch.send(f"{error._icon} **{error._category}** — {error.msg}")
        except Exception as e:
            print(f"[FDScript Error Logger] Failed to send error to channel: {e}")
    else:
        print(f"[FDScript Console Error] {error._category}: {error.msg}")
    
    raise FDAbortScript()


# ─────────────────────────────────────────────
# Bracket helpers
# ─────────────────────────────────────────────

def _find_matching_bracket(text: str, open_pos: int) -> int:
    depth = 0
    i = open_pos
    while i < len(text):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def _check_brackets(text: str) -> tuple[bool, str]:
    depth = 0
    for pos, ch in enumerate(text):
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
            if depth < 0:
                return False, f"Extra closing `]` at position {pos}"
    if depth > 0:
        return False, f"{'One unclosed' if depth == 1 else f'{depth} unclosed'} opening `[`"
    return True, ""


# ─────────────────────────────────────────────
# Timestamp helper
# ─────────────────────────────────────────────

_VALID_TIMESTAMP_FORMATS = {'t', 'T', 'd', 'D', 'f', 'F', 'R'}


def _build_timestamp(fmt: str) -> str | _FDError:
    fmt = fmt.strip() if fmt.strip() else 'T'
    if fmt not in _VALID_TIMESTAMP_FORMATS:
        return FDLogicError(
            f"`$addTimestamp` — invalid format `{fmt}`.\n"
            f"Valid formats: `t` `T` `d` `D` `f` `F` `R`"
        )
    return f'<t:{int(time.time())}:{fmt}>'


# ─────────────────────────────────────────────
# Reaction helpers
# ─────────────────────────────────────────────

_REACTIONS_MAX: int = 20
_CLEAR_DEFAULT: int = 10
_CLEAR_MAX:     int = 100


def _parse_reaction_emoji(raw: str) -> str | None:
    raw = raw.strip()
    if not raw:
        return None
    if re.match(r'^<a?:[a-zA-Z0-9_]+:\d+>$', raw):
        return raw
    return raw


def _extract_all_emojis(text: str) -> list[str]:
    custom_emoji_pattern = r'<a?:[a-zA-Z0-9_]+:\d+>'
    emoji_range = (
        r'[\U0001F300-\U0001F5FF'
        r'\U0001F600-\U0001F64F'
        r'\U0001F680-\U0001F6FF'
        r'\U0001F900-\U0001F9FF'
        r'\U0001FA70-\U0001FAFF'
        r'\u2600-\u26FF'
        r'\u2700-\u27BF]'
    )
    single_emoji = f'(?:{emoji_range}|[\U0001F1E6-\U0001F1FF]{{2}}|[0-9#*]\ufe0f?\u20e3)'
    modifier  = r'[\U0001F3FB-\U0001F3FF]'
    selector  = r'\ufe0f?'
    component = f'{single_emoji}{modifier}{selector}'
    unicode_emoji_pattern = f'{component}(?:\u200d{component})*'
    combined_pattern = f'({custom_emoji_pattern}|{unicode_emoji_pattern})'
    return re.findall(combined_pattern, text)


# ─────────────────────────────────────────────
# Log helpers
# ─────────────────────────────────────────────

_LOG_CHAR_LIMIT = 2000
_LOG_FILE_LIMIT = 10 * 1024 * 1024  # 10 MB


def _truncate(text: str, limit: int = 40) -> str:
    text = text.replace('\n', ' ')
    return text[:limit] + '…' if len(text) > limit else text


# ─────────────────────────────────────────────
# Uptime helper
# ─────────────────────────────────────────────

def _format_uptime(seconds: float) -> str:
    total = int(seconds)
    days,    total   = divmod(total, 86400)
    hours,   total   = divmod(total, 3600)
    minutes, secs    = divmod(total, 60)
    parts = []
    if days:    parts.append(f"{days}d")
    if hours:   parts.append(f"{hours}h")
    if minutes: parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return ' '.join(parts)


# ─────────────────────────────────────────────
# Embed helpers
# ─────────────────────────────────────────────

_NAMED_COLORS: dict[str, int] = {
    "red":0xE74C3C, "green":0x2ECC71, "blue":0x3498DB, "yellow":0xF1C40F,
    "orange":0xE67E22, "purple":0x9B59B6, "pink":0xFF69B4, "white":0xFFFFFF,
    "black":0x000000, "gray":0x95A5A6, "grey":0x95A5A6, "cyan":0x1ABC9C,
    "gold":0xF9A825, "navy":0x2C3E50, "lime":0x27AE60, "brown":0xA0522D,
    "teal":0x008080, "magenta":0xFF00FF, "blurple":0x5865F2, "dark":0x2B2D31,
}


def _parse_color(raw: str) -> int:
    raw = raw.strip().lower()
    if raw in _NAMED_COLORS:
        return _NAMED_COLORS[raw]
    try:
        return int(raw.lstrip("#"), 16)
    except ValueError:
        return 0x2B2D31


_NAMED_SEPARATORS: dict[str, str] = {
    "dot": ".", "com": ",", "apo": "'", "sem": ";", "colon": ":",
}


def _parse_separator(raw: str) -> str:
    return _NAMED_SEPARATORS.get(raw.strip(), raw.strip())


class _EmbedBuilder:
    def __init__(self):
        self.title:       str | None = None
        self.description: str | None = None
        self.color:       int | None = None
        self.footer:      str | None = None

    def is_set(self) -> bool:
        return any(v is not None for v in (self.title, self.description, self.color, self.footer))

    def build(self) -> discord.Embed:
        e = discord.Embed(
            title=self.title or "",
            description=self.description or "",
            color=self.color if self.color is not None else 0x2B2D31,
        )
        if self.footer:
            e.set_footer(text=self.footer)
        return e


# ─────────────────────────────────────────────
# DM helper
# ─────────────────────────────────────────────

async def _resolve_dm_target(
    target_str: str,
    ctx,
    ch: discord.abc.Messageable,
) -> discord.User | discord.Member | None:
    target_str = target_str.strip()
    mention_match = re.match(r'^<@!?(\d+)>$', target_str)
    if mention_match:
        user_id = int(mention_match.group(1))
    elif target_str.isdigit():
        user_id = int(target_str)
    else:
        await _send_error(ch, FDLogicError(
            f"`$dm` — invalid target: `{target_str}`.\n"
            f"Use a user ID or a mention (e.g. `<@123456789>`)."
        ))
        return None

    user = ctx.bot.get_user(user_id)
    if user is None:
        try:
            user = await ctx.bot.fetch_user(user_id)
        except discord.NotFound:
            await _send_error(ch, FDEnvironmentError(
                f"`$dm` — no user found with ID `{user_id}`"
            ))
            return None
        except discord.HTTPException as e:
            await _send_error(ch, FDRuntimeError(
                f"`$dm` — failed to fetch user `{user_id}`: `{e.text}`"
            ))
            return None
    return user


# ─────────────────────────────────────────────
# Guild helpers
# ─────────────────────────────────────────────

_CHANNEL_TYPES: dict[str, type] = {
    "text":     discord.TextChannel,
    "voice":    discord.VoiceChannel,
    "category": discord.CategoryChannel,
    "forum":    discord.ForumChannel,
    "stage":    discord.StageChannel,
    "all":      None,
}

_PERMISSION_NAMES: set[str] = {
    "admin","manage_guild","manage_roles","manage_channels","manage_messages",
    "manage_webhooks","manage_nicknames","manage_emojis","manage_threads",
    "manage_events","kick_members","ban_members","moderate_members",
    "mention_everyone","send_messages","send_tts_messages","embed_links",
    "attach_files","read_message_history","use_external_emojis",
    "use_external_stickers","add_reactions","connect","speak","mute_members",
    "deafen_members","move_members","use_voice_activation","priority_speaker",
    "stream","view_channel","view_audit_log","view_guild_insights",
    "change_nickname","create_instant_invite","request_to_speak",
    "use_application_commands","use_embedded_activities",
}


def _resolve_permission(raw: str) -> discord.Permissions | None | bool:
    raw = raw.strip().lower()
    if not raw or raw == "all":
        return None
    if raw.isdigit():
        return discord.Permissions(int(raw))
    if raw in _PERMISSION_NAMES:
        return discord.Permissions(**{raw: True})
    return False


# ─────────────────────────────────────────────
# Pending log entry
# ─────────────────────────────────────────────

class _PendingLog:
    def __init__(self, channel_id: int, name_code: str, entries: list[str]):
        self.channel_id = channel_id
        self.name_code  = name_code
        self.entries    = entries


# ─────────────────────────────────────────────
# Reply Wrapper
# ─────────────────────────────────────────────

class _ReplyWrapper:
    """Wraps a channel so that .send() becomes .reply() transparently."""
    def __init__(self, message: discord.Message):
        self._message = message

    async def send(self, *args, **kwargs):
        return await self._message.reply(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._message.channel, name)


# ─────────────────────────────────────────────
# Execution Context
# ─────────────────────────────────────────────





class ExecutionContext:
    def __init__(self, message: discord.Message = None, bot: discord.Client = None, member: discord.Member = None, is_event: bool = False):
        self.bot = bot
        self.is_event = is_event
        self.temp_vars: dict = {}
        self._typing_task: asyncio.Task | None = None
        self.last_bot_message: discord.Message | None = None
        self.execution_log: list[str] = []
        self._log_step: int = 0
        self._pending_logs: list[_PendingLog] = []
        self._last_log_step: int = 0
        self.embed_builder: _EmbedBuilder = _EmbedBuilder()
        self.return_vars: dict = {}
        self.dm_target: discord.User | discord.Member | None = None

        if message is not None:
            self.message = message
            self.builtins: dict = {
                "authorID":    str(message.author.id),
                "authorName":  message.author.name,
                "botID":       str(bot.user.id) if bot.user else "",
                "botName":     bot.user.name if bot.user else "",
                "channelID":   str(message.channel.id),
                "channelName": message.channel.name,
                "guildID":     str(message.guild.id) if message.guild else "DM",
                "guildName":   message.guild.name if message.guild else "DM",
                "mention":     message.author.mention,
            }
        elif member is not None:
            guild = member.guild
            channel = guild.system_channel or (guild.text_channels[0] if guild.text_channels else None)
            
            class DummyMessage:
                def __init__(self):
                    self.id = 0
                    self.author = member
                    self.channel = channel
                    self.guild = guild
                    self.content = ""
            
            self.message = DummyMessage()
            
            self.builtins: dict = {
                "authorID":    str(member.id),
                "authorName":  member.name,
                "botID":       str(bot.user.id) if bot.user else "",
                "botName":     bot.user.name if bot.user else "",
                "channelID":   str(channel.id) if channel else "",
                "channelName": channel.name if channel else "",
                "guildID":     str(guild.id) if guild else "Unknown Guild",
                "guildName":   guild.name if guild else "Unknown Guild",
                "mention":     member.mention,
            }
        else:
            self.message = None
            self.builtins = {}

    def log_event(self, entry: str):
        self._log_step += 1
        self.execution_log.append(f"{self._log_step}. {entry}")

    def snapshot_log(self, channel_id: int, name_code: str):
        slice_entries = self.execution_log[self._last_log_step:]
        self._pending_logs.append(_PendingLog(channel_id, name_code, list(slice_entries)))
        self._last_log_step = len(self.execution_log)

    def get_var(self, name: str) -> str:
        name = name.strip()
        if name in self.temp_vars:
            return str(self.temp_vars[name])
        if name in self.builtins:
            return str(self.builtins[name])
        return ""

    def set_var(self, name: str, value: str):
        self.temp_vars[name.strip()] = value

    def start_typing(self, channel: discord.TextChannel):
        async def _keep_typing():
            try:
                async with channel.typing():
                    await asyncio.Future()
            except asyncio.CancelledError:
                pass
        self._typing_task = asyncio.create_task(_keep_typing())

    def stop_typing(self):
        if self._typing_task:
            self._typing_task.cancel()
            self._typing_task = None

    async def get_dest(self) -> discord.abc.Messageable:
        if self.dm_target is not None:
            return await self.dm_target.create_dm()
        if getattr(self, 'is_global_reply', False):
            return _ReplyWrapper(self.message)
        return self.message.channel

    # ── Expression resolver ─────────────────────────────────────────

    def resolve(self, text: str) -> str:
        if not text:
            return text
        return self._resolve_pass(text)

    def _resolve_pass(self, text: str) -> str:
        result: list[str] = []
        i = 0
        n = len(text)

        while i < n:
            if text[i] != '$':
                result.append(text[i])
                i += 1
                continue

            j = i + 1
            while j < n and (text[j].isalnum() or text[j] == '_'):
                j += 1

            cmd_name = text[i + 1:j]
            if not cmd_name:
                result.append('$')
                i += 1
                continue

            if j < n and text[j] == '[':
                bracket_end = _find_matching_bracket(text, j)
                if bracket_end == -1:
                    result.append(FDRuntimeError(f"Unclosed bracket in: ${cmd_name}[").msg)
                    i = j + 1
                    continue
                inner_raw = text[j + 1:bracket_end]
                inner = self._resolve_pass(inner_raw)
                resolved = self._apply_cmd(cmd_name, inner)
                result.append(resolved)
                i = bracket_end + 1
            else:
                val = self._resolve_bare(cmd_name)
                if val is not None:
                    result.append(val)
                    i = j
                else:
                    result.append('$')
                    i += 1

        return ''.join(result)

    def _resolve_bare(self, cmd_name: str) -> str | None:
        import time as _time
        if cmd_name == 'messageID':
            return str(self.message.id)
        if cmd_name == 'message':
            full = self.message.content.strip()
            if getattr(self, 'is_event', False):
                return full
            parts = full.split(None, 1)
            return parts[1] if len(parts) > 1 else ""
        if cmd_name == 'randomUserID':
            guild = self.message.guild
            if guild:
                members = [m for m in guild.members if not m.bot]
                if members:
                    return str(random.choice(members).id)
            return ""
        if cmd_name == 'addTimestamp':
            return f'<t:{int(_time.time())}:T>'
        if cmd_name == 'uptime':
            if _BOT_START_TIME == 0.0:
                return ""
            return _format_uptime(_time.time() - _BOT_START_TIME)
        if cmd_name == 'ping':
            return f"{round(self.bot.latency * 1000)}ms"
        if cmd_name == 'return':
            return None
        if cmd_name in self.builtins:
            return str(self.builtins[cmd_name])
        # ── Plugin inline resolver (registered by FDScript) ──────
        if _inline_resolver is not None:
            val = _inline_resolver(cmd_name, [], self)
            if val is not None:
                return val
        return None

    def _apply_cmd(self, cmd_name: str, inner: str) -> str:
        if cmd_name == 'var':
            return self.get_var(inner.strip())
        if cmd_name == 'return':
            key = inner.strip()
            if not key:
                return FDLogicError("`$return[]` — variable name cannot be empty").msg
            if key not in self.return_vars:
                return FDRuntimeError(
                    f"`$return[{key}]` — `{key}` has no value stored by any `$returnXxx` command"
                ).msg
            return str(self.return_vars[key])
        if cmd_name in ('sum', 'sub', 'mul', 'div', 'mod'):
            parts = [x.strip() for x in inner.split(';')]
            if len(parts) != 2:
                return FDRuntimeError("Wrong number of arguments in math operation").msg
            try:
                a, b = float(parts[0]), float(parts[1])
                if cmd_name == 'sum':  res = a + b
                elif cmd_name == 'sub': res = a - b
                elif cmd_name == 'mul': res = a * b
                elif cmd_name == 'div':
                    if b == 0:
                        return FDRuntimeError("Division by zero").msg
                    res = a / b
                elif cmd_name == 'mod': res = a % b
                return str(int(res)) if float(res).is_integer() else str(res)
            except ValueError:
                return FDRuntimeError("Non-numeric value in math operation").msg
        if cmd_name == 'randomint':
            parts = [x.strip() for x in inner.split(';')]
            if len(parts) == 2:
                try:
                    a, b = int(float(parts[0])), int(float(parts[1]))
                    return str(random.randint(min(a, b), max(a, b)))
                except Exception:
                    return FDRuntimeError("Non-numeric arguments in randomint").msg
            return FDLogicError("randomint requires two arguments: $randomint[min; max]").msg
        if cmd_name == 'randomstr':
            parts = [p.strip() for p in inner.split(';') if p.strip()]
            return random.choice(parts) if parts else ""
        # ── Plugin inline resolver (registered by FDScript) ──────
        if _inline_resolver is not None:
            args = [x.strip() for x in inner.split(';')] if inner.strip() else []
            val = _inline_resolver(cmd_name, args, self)
            if val is not None:
                return val
        return f"${cmd_name}[{inner}]"


# ─────────────────────────────────────────────
# Lexer
# ─────────────────────────────────────────────

class Command:
    def __init__(self, name: str, args: list[str], raw: str):
        self.name = name
        self.args = args
        self.raw  = raw


def _strip_inline_comment(line: str) -> str:
    depth = 0
    for i, ch in enumerate(line):
        if ch == '[':
            depth += 1
        elif ch == ']':
            depth -= 1
        elif ch == '#' and depth == 0:
            return line[:i].rstrip()
    return line


def tokenise(line: str) -> 'Command | str | None':
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    line = _strip_inline_comment(line)
    if not line:
        return None
    if not line.startswith("$"):
        return line

    body = line[1:]
    if body in {"else", "endif", "endwhile", "endfor", "break"}:
        return Command(body, [], line)

    bracket_pos = body.find("[")
    if bracket_pos == -1:
        name = body
        if name not in KNOWN_COMMANDS:
            return Command("__unknown__", [name], line)
        return Command(name, [], line)

    name = body[:bracket_pos].strip()
    if name not in KNOWN_COMMANDS:
        return Command("__unknown__", [name], line)

    rest = body[bracket_pos:]
    valid, err_msg = _check_brackets(rest)
    if not valid:
        raise SyntaxError(f"Bracket error in `{name}`: {err_msg}")

    inner = rest[1:-1]
    args  = _split_args(inner)
    return Command(name, args, line)


def _split_args(inner: str) -> list[str]:
    args = []
    depth = 0
    current = []
    for ch in inner:
        if ch == "[":
            depth += 1
            current.append(ch)
        elif ch == "]":
            depth -= 1
            current.append(ch)
        elif ch == ";" and depth == 0:
            args.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        args.append("".join(current).strip())
    return args


# ─────────────────────────────────────────────
# Multi-token line tokenizer
# ─────────────────────────────────────────────

_INLINE_VARS: set[str] = {
    'message', 'messageID', 'ping', 'uptime', 'mention',
    'authorID', 'authorName', 'botID', 'botName',
    'channelID', 'channelName', 'guildID', 'guildName',
    'addTimestamp', 'randomUserID',
}


_INLINE_WITH_ARGS: set[str] = {
    'message', 'var', 'return',
    'randomint', 'randomstr',
    'sum', 'sub', 'mul', 'div', 'mod',
    'replaceText',
}


def tokenise_line(line: str) -> list:
    line = line.strip()
    if not line or line.startswith('#'):
        return []
    line = _strip_inline_comment(line)
    if not line:
        return []

    tokens:   list       = []
    text_buf: list[str]  = []
    i            = 0
    n            = len(line)
    at_boundary  = True

    def flush_text() -> None:
        nonlocal text_buf
        chunk = ''.join(text_buf).strip()
        if chunk:
            tokens.append(chunk)
        text_buf = []

    while i < n:
        ch = line[i]

        if ch in (' ', '\t'):
            text_buf.append(ch)
            at_boundary = True
            i += 1
            continue

        if ch == '$' and at_boundary:
            j = i + 1
            while j < n and (line[j].isalnum() or line[j] == '_'):
                j += 1
            cmd_name = line[i + 1:j]

            is_control = cmd_name in {'else', 'endif', 'endwhile', 'endfor', 'break'}
            is_known   = cmd_name in KNOWN_COMMANDS or is_control

            if cmd_name and is_known:
                flush_text()

                if j >= n or line[j] != '[':
                    if cmd_name in _INLINE_VARS:
                        text_buf.append(f'${cmd_name}')
                        i = j
                        at_boundary = False
                        continue
                    flush_text()
                    tokens.append(Command(cmd_name, [], f'${cmd_name}'))
                    i = j
                    at_boundary = True
                    continue

                bracket_end = _find_matching_bracket(line, j)
                if bracket_end == -1:
                    tokens.append(Command(
                        '__syntax_error__',
                        [f'Unclosed bracket in `${cmd_name}`'],
                        f'${cmd_name}['
                    ))
                    i = j + 1
                    at_boundary = False
                    continue

                inner = line[j + 1:bracket_end]
                ok, err_msg = _check_brackets(f'[{inner}]')
                if not ok:
                    tokens.append(Command(
                        '__syntax_error__',
                        [f'Bracket error in `{cmd_name}`: {err_msg}'],
                        line
                    ))
                    i = bracket_end + 1
                    at_boundary = True
                    continue
                
                if cmd_name in _INLINE_WITH_ARGS:
                    text_buf.append(f'${cmd_name}[{inner}]')
                    i = bracket_end + 1
                    at_boundary = False
                    continue

                tokens.append(Command(cmd_name, _split_args(inner), f'${cmd_name}[{inner}]'))
                i = bracket_end + 1
                at_boundary = True
                continue

            if cmd_name and not is_known:
                flush_text()
                tokens.append(Command('__unknown__', [cmd_name], f'${cmd_name}'))
                i = j
                at_boundary = True
                continue

        text_buf.append(ch)
        at_boundary = False
        i += 1

    flush_text()
    return tokens