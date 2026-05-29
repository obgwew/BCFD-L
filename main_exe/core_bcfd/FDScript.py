# FDScript.py - FDScript Interpreter for Discord Bots
import asyncio
import discord
import io
import json
import os
import re
import random
import time

# ─────────────────────────────────────────────
# Persistent storage
# ─────────────────────────────────────────────

_VARS_DIR: str = ''
_BOT_START_TIME: float = 0.0


def set_bot_start_time(t: float):
    global _BOT_START_TIME
    _BOT_START_TIME = t

# ─────────────────────────────────────────────
# Reserved Names
# ─────────────────────────────────────────────

KNOWN_COMMANDS: set[str] = {
    #a
    "addBotReactions","addTimestamp","addUserReactions","and","authorID",
    "authorName",
    #b
    "botID","botName","break",
    #c
    "channelID","channelName","clear","clientTyping","color",
    #d
    "deletecommand","description","div","dm",
    #e
    "elif","else","endfor","endif",
    "endwhile",
    #f
    "footer","for",
    #g
    "getVar","guildName",
    #i
    "if",
    #l
    "log",
    #m
    "mention","message","messageID","mod","mul",
    #o
    "or",
    #p
    "ping",
    #r
    "randomint","randomstr","randomUserID","return",
    "returnGuildChannelsID","returnGuildRolesID","returnGuildUsersID",
    "returnGetReactions",
    #s
    "sendEmbedMessage","sendMessage","setVar","strictArgs","sub","sum",
    #t
    "title",
    #u
    "uptime",
    #v
    "var",
    #w
    "while",
}

def set_vars_dir(path: str):
    global _VARS_DIR
    _VARS_DIR = path


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
            json.dump({'name': name, 'value': str(value)},
                      f, ensure_ascii=False, indent=2)


class StopExecution(Exception):
    pass


# ─────────────────────────────────────────────
# ► Error System
# ─────────────────────────────────────────────

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


async def _send_error(channel: discord.abc.Messageable, error: _FDError) -> None:
    await channel.send(f"{error._icon} **{error._category}:** {error.msg}")


# ─────────────────────────────────────────────
# ► Bracket Helpers
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
# Timestamp Helper
# ─────────────────────────────────────────────

_VALID_TIMESTAMP_FORMATS = {'t', 'T', 'd', 'D', 'f', 'F', 'R'}

def _build_timestamp(fmt: str) -> str | _FDError:
    fmt = fmt.strip() if fmt.strip() else 'T'
    if fmt not in _VALID_TIMESTAMP_FORMATS:
        return FDLogicError(
            f"`$addTimestamp` — invalid format `{fmt}`.\n"
            f"Valid formats: `t` `T` `d` `D` `f` `F` `R`"
        )
    now = int(time.time())
    return f'<t:{now}:{fmt}>'


# ─────────────────────────────────────────────
# ► Reaction Helper
# ─────────────────────────────────────────────

_REACTIONS_MAX: int = 20
_CLEAR_DEFAULT: int = 10
_CLEAR_MAX:     int = 100

# ------ Validate and normalise a single emoji string ------
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
        r'[\U0001F300-\U0001F5FF' # Symbols & Pictographs
        r'\U0001F600-\U0001F64F'  # Emoticons
        r'\U0001F680-\U0001F6FF'  # Transport & Map
        r'\U0001F900-\U0001F9FF'  # Supplemental Symbols
        r'\U0001FA70-\U0001FAFF'  # Symbols Extended-A
        r'\u2600-\u26FF'          # Misc Symbols
        r'\u2700-\u27BF]'         # Dingbats
    )
    
    single_emoji = f'(?:{emoji_range}|[\U0001F1E6-\U0001F1FF]{2}|[0-9#*]\ufe0f?\u20e3)'
    modifier = r'[\U0001F3FB-\U0001F3FF]?'  
    selector = r'\ufe0f?'                 
    
    component = f'{single_emoji}{modifier}{selector}'
    
    unicode_emoji_pattern = f'{component}(?:\u200d{component})*'
    
    combined_pattern = f'({custom_emoji_pattern}|{unicode_emoji_pattern})'
    
    return re.findall(combined_pattern, text)


# ─────────────────────────────────────────────
# ► Log Helper
# ─────────────────────────────────────────────

_LOG_CHAR_LIMIT = 2000
_LOG_FILE_LIMIT = 10 * 1024 * 1024  # 10 MB
_LOG_HEADER     = "```\n[FDScript Log]\n"
_LOG_FOOTER     = "\n```"

def _truncate(text: str, limit: int = 40) -> str:
    """Shorten a string for log display."""
    text = text.replace('\n', ' ')
    return text[:limit] + '…' if len(text) > limit else text


# ─────────────────────────────────────────────
# ► UpTime Helper
# ─────────────────────────────────────────────

def _format_uptime(seconds: float) -> str:
    """Convert a duration in seconds to a human-readable string like 3d 4h 12m 7s."""
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
# ► Embed Helper
# ─────────────────────────────────────────────

_NAMED_COLORS: dict[str, int] = {
    "red":       0xE74C3C,
    "green":     0x2ECC71,
    "blue":      0x3498DB,
    "yellow":    0xF1C40F,
    "orange":    0xE67E22,
    "purple":    0x9B59B6,
    "pink":      0xFF69B4,
    "white":     0xFFFFFF,
    "black":     0x000000,
    "gray":      0x95A5A6,
    "grey":      0x95A5A6,
    "cyan":      0x1ABC9C,
    "gold":      0xF9A825,
    "navy":      0x2C3E50,
    "lime":      0x27AE60,
    "brown":     0xA0522D,
    "teal":      0x008080,
    "magenta":   0xFF00FF,
    "blurple":   0x5865F2,
    "dark":      0x2B2D31,
}


def _parse_color(raw: str) -> int:
    """Parse a hex string (#RRGGBB or RRGGBB) or a named color → int."""
    raw = raw.strip().lower()
    if raw in _NAMED_COLORS:
        return _NAMED_COLORS[raw]
    try:
        return int(raw.lstrip("#"), 16)
    except ValueError:
        return 0x2B2D31


# Named separators — "sem" must always be written by name, never as raw ";"
_NAMED_SEPARATORS: dict[str, str] = {
    "dot":   ".",
    "com":   ",",
    "apo":   "'",
    "sem":   ";",
    "colon": ":",
}


def _parse_separator(raw: str) -> str:
    """Resolve a separator name or literal to its string value."""
    stripped = raw.strip()
    return _NAMED_SEPARATORS.get(stripped, stripped)


class _EmbedBuilder:
    """Holds embed fields set via $title / $description / $color / $footer."""
    def __init__(self):
        self.title:       str | None = None
        self.description: str | None = None
        self.color:       int | None = None
        self.footer:      str | None = None

    def is_set(self) -> bool:
        return any(v is not None for v in (
            self.title, self.description, self.color, self.footer
        ))

    def build(self) -> discord.Embed:
        e = discord.Embed(
            title=self.title or "",
            description=self.description or "",
            color=self.color if self.color is not None else 0x2B2D31,
        )
        if self.footer:
            e.set_footer(text=self.footer)
        return e


async def _resolve_dm_target(
    target_str: str,
    ctx,
    ch: discord.abc.Messageable,
) -> discord.User | discord.Member | None:
    """
    Parse a user ID or mention string and return the corresponding User/Member.
    Sends an error to `ch` and returns None on failure.
    """
    target_str = target_str.strip()

    mention_match = re.match(r'^<@!?(\d+)>$', target_str)
    if mention_match:
        user_id = int(mention_match.group(1))
    elif target_str.isdigit():
        user_id = int(target_str)
    else:
        await _send_error(ch, FDLogicError(
            f"`$dm` — invalid target: `{target_str}`.\n"
            f"Use a user ID (e.g. `123456789`) or a mention (e.g. `<@123456789>`)."
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
# ► Guild Helpers
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
    "admin", "manage_guild", "manage_roles", "manage_channels",
    "manage_messages", "manage_webhooks", "manage_nicknames", "manage_emojis",
    "manage_threads", "manage_events", "kick_members", "ban_members",
    "moderate_members", "mention_everyone", "send_messages", "send_tts_messages",
    "embed_links", "attach_files", "read_message_history", "use_external_emojis",
    "use_external_stickers", "add_reactions", "connect", "speak", "mute_members",
    "deafen_members", "move_members", "use_voice_activation", "priority_speaker",
    "stream", "view_channel", "view_audit_log", "view_guild_insights",
    "change_nickname", "create_instant_invite", "request_to_speak",
    "use_application_commands", "use_embedded_activities",
}


def _resolve_permission(raw: str) -> discord.Permissions | None:
    raw = raw.strip().lower()
    if not raw or raw == "all":
        return None
    if raw.isdigit():
        return discord.Permissions(int(raw))
    if raw in _PERMISSION_NAMES:
        return discord.Permissions(**{raw: True})
    return False


# ─────────────────────────────────────────────
# ► Pending Log Entry
# ─────────────────────────────────────────────

class _PendingLog:
    """A snapshot taken at $log time, to be flushed after execution ends."""
    def __init__(self, channel_id: int, name_code: str, entries: list[str]):
        self.channel_id = channel_id
        self.name_code  = name_code
        self.entries    = entries


# ─────────────────────────────────────────────
# Execution Context
# ─────────────────────────────────────────────

class ExecutionContext:
    def __init__(self, message: discord.Message, bot: discord.Client):
        self.message = message
        self.bot = bot
        self.temp_vars: dict = {}
        self._typing_task: asyncio.Task | None = None

        # ── Last bot message sent during this execution ───────────────
        self.last_bot_message: discord.Message | None = None

        # ── Execution log ────────────────────────────────────────────
        self.execution_log: list[str] = []
        self._log_step: int = 0

        # ── Pending $log snapshots (flushed after full execution) ─────
        self._pending_logs: list[_PendingLog] = []
        self._last_log_step: int = 0

        # ── Embed builder (flushed after full execution) ──────────────
        self.embed_builder: _EmbedBuilder = _EmbedBuilder()

        # ── Return vars — exclusive to $returnXxx family ──────────────
        self.return_vars: dict = {}

        # ── DM target — set by $dm[userID], None = send to channel ────
        self.dm_target: discord.User | discord.Member | None = None

        self.builtins: dict = {
            "authorID":    str(message.author.id),
            "authorName":  message.author.name,
            "botID":       str(bot.user.id) if bot.user else "",
            "botName":     bot.user.name if bot.user else "",
            "channelID":   str(message.channel.id),
            "channelName": message.channel.name,
            "guildName":   message.guild.name if message.guild else "DM",
            "mention":     message.author.mention,
        }

    # ------ Log event ------
    def log_event(self, entry: str):
        self._log_step += 1
        self.execution_log.append(f"{self._log_step}. {entry}")

    # ------ Snapshot: capture entries since the last $log ------
    def snapshot_log(self, channel_id: int, name_code: str):
        slice_entries = self.execution_log[self._last_log_step:]
        self._pending_logs.append(
            _PendingLog(channel_id, name_code, list(slice_entries))
        )
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

    # ------ Resolve plain-text send destination ------
    async def get_dest(self) -> discord.abc.Messageable:
        """Returns DM channel if dm_target is set, otherwise the message channel."""
        if self.dm_target is not None:
            return await self.dm_target.create_dm()
        return self.message.channel

    # ── Sequential resolver — supports deep nesting ─────────────────

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
                    result.append(
                        FDRuntimeError(f"Unclosed bracket in: ${cmd_name}[").msg
                    )
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
        if cmd_name == 'messageID':
            return str(self.message.id)

        if cmd_name == 'message':
            full = self.message.content.strip()
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
            now = int(time.time())
            return f'<t:{now}:T>'

        if cmd_name == 'uptime':
            if _BOT_START_TIME == 0.0:
                return ""
            return _format_uptime(time.time() - _BOT_START_TIME)

        if cmd_name == 'ping':
            return f"{round(self.bot.latency * 1000)}ms"

        if cmd_name == 'return':
            return None

        if cmd_name in self.builtins:
            return str(self.builtins[cmd_name])

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

        if cmd_name == 'getVar':
            data = _load_data()
            return str(data.get(inner.strip(), ""))

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

        return f"${cmd_name}[{inner}]"


# ─────────────────────────────────────────────
# Lexer
# ─────────────────────────────────────────────

class Command:
    def __init__(self, name: str, args: list[str], raw: str):
        self.name = name
        self.args = args
        self.raw = raw


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


def tokenise(line: str) -> Command | str | None:
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
    args = _split_args(inner)
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
# Interpreter
# ─────────────────────────────────────────────

class Interpreter:
    def __init__(self, script: str):
        self.source_lines = script.splitlines()

    # ------ Main entry point ------
    async def run(self, ctx: ExecutionContext):
        tokens = self._tokenise_all()
        errors = self._validate(tokens)
        if errors:
            lines = "\n".join(
                f"{e._icon} **{e._category}** — {e.msg}" for e in errors
            )
            await ctx.message.channel.send(
                f"**{'One error' if len(errors) == 1 else f'{len(errors)} errors'} found in script, execution aborted:**\n{lines}"
            )
            return
        await self._execute(tokens, ctx)
        await self._flush_embed(ctx)
        await self._flush_logs(ctx)

    # ------ Send embed from builder if set ------
    async def _flush_embed(self, ctx: ExecutionContext):
        if not ctx.embed_builder.is_set():
            return
        ch = ctx.message.channel
        ctx.stop_typing()
        sent = await ch.send(embed=ctx.embed_builder.build())
        ctx.last_bot_message = sent
        ctx.log_event("embed builder → sent")

    # ------ Send all pending log snapshots ------
    async def _flush_logs(self, ctx: ExecutionContext):
        ch = ctx.message.channel

        for pending in ctx._pending_logs:
            target_ch = ctx.bot.get_channel(pending.channel_id)
            if not target_ch:
                await _send_error(ch, FDEnvironmentError(
                    f"`$log` — channel `{pending.channel_id}` not found or bot has no access"
                ))
                continue

            label = f"[FDScript Log{f' — {pending.name_code}' if pending.name_code else ''}]"
            body  = "\n".join(pending.entries) if pending.entries else "(no events in this range)"
            full_text = f"{label}\n{body}"

            block = f"```\n{full_text}\n```"

            if len(block) <= _LOG_CHAR_LIMIT:
                await target_ch.send(block)
            else:
                raw_bytes = full_text.encode("utf-8")
                if len(raw_bytes) > _LOG_FILE_LIMIT:
                    await _send_error(ch, FDRuntimeError(
                        f"`$log` — log snapshot exceeds the 10 MB file limit and cannot be sent"
                    ))
                    continue
                safe_name = (
                    ''.join(c if c.isalnum() or c in ('-', '_') else '_'
                             for c in pending.name_code).strip('_')
                    or "fdscript_log"
                )
                filename = f"{safe_name}.txt"
                file_obj = discord.File(
                    fp=io.BytesIO(raw_bytes),
                    filename=filename,
                )
                await target_ch.send(
                    f"📄 Log snapshot too large for a code block — sent as file:",
                    file=file_obj,
                )

    # ------ Tokenise every line upfront ------
    def _tokenise_all(self) -> list:
        result = []
        for line in self.source_lines:
            try:
                tok = tokenise(line)
                if tok is not None:
                    result.append(tok)
            except SyntaxError as e:
                result.append(Command("__syntax_error__", [str(e)], line))
        return result

    # ------ Validate — returns list[_FDError] ------
    def _validate(self, tokens: list) -> list[_FDError]:
        errors: list[_FDError] = []
        stack = []

        OPENERS = {"if": "endif", "while": "endwhile", "for": "endfor"}
        CLOSERS = {"endif": "if", "endwhile": "while", "endfor": "for"}

        for i, tok in enumerate(tokens):
            line_num = i + 1

            if isinstance(tok, Command) and tok.name == "__syntax_error__":
                errors.append(FDSyntaxError(f"Line {line_num}: {tok.args[0]}"))
                continue

            if isinstance(tok, Command) and tok.name == "__unknown__":
                errors.append(FDSyntaxError(f"Line {line_num}: Unknown command `{tok.args[0]}`"))
                continue

            if isinstance(tok, str):
                continue

            if tok.name in OPENERS:
                stack.append((tok.name, line_num))
                continue

            if tok.name in CLOSERS:
                expected = CLOSERS[tok.name]
                if not stack:
                    errors.append(FDSyntaxError(
                        f"Line {line_num}: `${tok.name}` without `${expected}`"
                    ))
                elif stack[-1][0] != expected:
                    errors.append(FDLogicError(
                        f"Line {line_num}: `${tok.name}` does not match "
                        f"`${stack[-1][0]}` opened at line {stack[-1][1]}"
                    ))
                    stack.pop()
                else:
                    stack.pop()
                continue

            if tok.name == "break":
                in_loop = any(t[0] in ("while", "for") for t in stack)
                if not in_loop:
                    errors.append(FDLogicError(
                        f"Line {line_num}: `$break` outside `$while` or `$for`"
                    ))
                continue

            if tok.name == "log":
                if not tok.args or not tok.args[0].strip():
                    errors.append(FDLogicError(
                        f"Line {line_num}: `$log` requires at least a channel ID: "
                        f"`$log[channelID]` or `$log[channelID; name_code]`"
                    ))
                continue

            if tok.name == "dm" and tok.args and not any(a.strip() for a in tok.args):
                errors.append(FDLogicError(
                    f"Line {line_num}: `$dm[]` — target cannot be empty. "
                    f"Provide a user ID or mention, or use `$dm` (no brackets) "
                    f"to DM the command author."
                ))
                continue

        for opener, line_num in stack:
            errors.append(FDSyntaxError(
                f"Line {line_num}: `${opener}` not closed with `${OPENERS[opener]}`"
            ))

        return errors

    # ------ Execute ------
    async def _execute(self, tokens: list, ctx: ExecutionContext, start: int = 0) -> int:
        i = start
        while i < len(tokens):
            tok = tokens[i]
            i += 1

            if isinstance(tok, str):
                ctx.stop_typing()
                dest = await ctx.get_dest()
                sent = await dest.send(ctx.resolve(tok))
                ctx.last_bot_message = sent
                continue

            if tok.name == "if":
                i = await self._exec_if(tokens, i - 1, ctx)
                continue
            if tok.name == "while":
                i = await self._exec_while(tokens, i - 1, ctx)
                continue
            if tok.name == "for":
                i = await self._exec_for(tokens, i - 1, ctx)
                continue
            if tok.name in ("endif", "endwhile", "endfor", "elif", "else"):
                return i - 1
            if tok.name == "break":
                return -1

            await self._exec_command(tok, ctx)

        return i

    # ------ if / elif / else / endif ------
    async def _exec_if(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        i = start
        branch_taken = False

        while i < len(tokens):
            tok = tokens[i]

            if tok.name in ("if", "elif"):
                cond_str = tok.args[0] if tok.args else ""
                cond_val = self._evaluate(cond_str, ctx)
                label = "if" if tok.name == "if" else "elif"
                ctx.log_event(f"{label} [{cond_str}] → {'✓' if cond_val else '✗'}")
                i += 1
                execute = not branch_taken and cond_val
                if execute:
                    branch_taken = True
                i = await self._run_block_until(
                    tokens, i, {"elif", "else", "endif"}, ctx, execute=execute
                )
                if i == "break":
                    return "break"
                continue

            if tok.name == "else":
                ctx.log_event(f"else → {'taken' if not branch_taken else 'skipped'}")
                i += 1
                i = await self._run_block_until(
                    tokens, i, {"endif"}, ctx, execute=not branch_taken
                )
                if i == "break":
                    return "break"
                continue

            if tok.name == "endif":
                return i + 1

            i += 1

        return i

    # ------ while / endwhile ------
    async def _exec_while(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        tok = tokens[start]
        cond_str = tok.args[0] if tok.args else ""
        body_start = start + 1
        body_end = self._find_closer(tokens, body_start, "while", "endwhile")

        iterations = 0
        while self._evaluate(cond_str, ctx):
            iterations += 1
            result = await self._run_block_slice(tokens, body_start, body_end, ctx)
            if result == "break":
                break

        ctx.log_event(f"while [{cond_str}] → {iterations} iter{'s' if iterations != 1 else ''}")
        return body_end + 1

    # ------ for / endfor ------
    async def _exec_for(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        tok = tokens[start]
        count_str = ctx.resolve(tok.args[0]) if tok.args else "0"

        try:
            count = int(count_str)
        except ValueError:
            await _send_error(
                ctx.message.channel,
                FDRuntimeError(f"`$for` expects an integer, got: `{count_str}`")
            )
            count = 0

        body_start = start + 1
        body_end = self._find_closer(tokens, body_start, "for", "endfor")

        for _ in range(count):
            result = await self._run_block_slice(tokens, body_start, body_end, ctx)
            if result == "break":
                break

        ctx.log_event(f"for [{count}] → {count} iter{'s' if count != 1 else ''}")
        return body_end + 1

    # ------ _run_block_until ------
    async def _run_block_until(
        self,
        tokens: list,
        start: int,
        stoppers: set,
        ctx: ExecutionContext,
        execute: bool,
    ) -> int:
        i = start
        depth = 0
        while i < len(tokens):
            tok = tokens[i]

            if not isinstance(tok, str):
                if tok.name in ("if", "while", "for"):
                    depth += 1
                elif tok.name in ("endif", "endwhile", "endfor"):
                    if depth > 0:
                        depth -= 1
                    elif tok.name in stoppers:
                        return i
                elif depth == 0 and tok.name in stoppers:
                    return i

            if execute and depth == 0:
                if isinstance(tok, str):
                    ctx.stop_typing()
                    dest = await ctx.get_dest()
                    sent = await dest.send(ctx.resolve(tok))
                    ctx.last_bot_message = sent
                elif tok.name not in stoppers:
                    if tok.name == "break":
                        return "break"
                    elif tok.name == "if":
                        i = await self._exec_if(tokens, i, ctx)
                        if i == "break":
                            return "break"
                        continue
                    elif tok.name == "while":
                        i = await self._exec_while(tokens, i, ctx)
                        continue
                    elif tok.name == "for":
                        i = await self._exec_for(tokens, i, ctx)
                        continue
                    else:
                        await self._exec_command(tok, ctx)
            i += 1

        return i

    # ------ _run_block_slice ------
    async def _run_block_slice(
        self, tokens: list, start: int, end: int, ctx: ExecutionContext
    ) -> str | None:
        i = start
        while i < end:
            tok = tokens[i]
            i += 1

            if isinstance(tok, str):
                ctx.stop_typing()
                dest = await ctx.get_dest()
                sent = await dest.send(ctx.resolve(tok))
                ctx.last_bot_message = sent
                continue

            if tok.name == "break":
                return "break"

            if tok.name == "if":
                res = await self._exec_if(tokens, i - 1, ctx)
                if res == "break":
                    return "break"
                i = res
            elif tok.name == "while":
                i = await self._exec_while(tokens, i - 1, ctx)
            elif tok.name == "for":
                i = await self._exec_for(tokens, i - 1, ctx)
            else:
                await self._exec_command(tok, ctx)

        return None

    # ------ _find_closer ------
    def _find_closer(self, tokens: list, start: int, opener: str, closer: str) -> int:
        depth = 0
        i = start
        while i < len(tokens):
            tok = tokens[i]
            if not isinstance(tok, str):
                if tok.name == opener:
                    depth += 1
                elif tok.name == closer:
                    if depth == 0:
                        return i
                    depth -= 1
            i += 1
        return i

    # ------ Execute a single command ------
    async def _exec_command(self, cmd: Command, ctx: ExecutionContext):
        name = cmd.name
        args = [ctx.resolve(a) for a in cmd.args]
        ch   = ctx.message.channel

        # ── clientTyping ─────────────────────────────────────────────
        if name == "clientTyping":
            ctx.start_typing(ch)
            ctx.log_event("clientTyping → started")
            return

        # ── addUserReactions ──────────────────────────────────────────
        if name == "addUserReactions":
            if not args:
                await _send_error(ch, FDLogicError(
                    "`$addUserReactions` requires at least one emoji argument"
                ))
                return

            # 💡 الذكاء كله هنا: نحل المتغيرات، ندمج كل شيء، ثم نستخرج الإيموجيات الصالحة فقط
            resolved_text = "".join(ctx.resolve(arg) for arg in args)
            emojis_to_add = _extract_all_emojis(resolved_text)

            if not emojis_to_add:
                ctx.log_event("تنبيه: لم يتم العثور على أي إيموجيات صالحة في أمر $addUserReactions")
                return

            if len(emojis_to_add) > _REACTIONS_MAX:
                await _send_error(ch, FDLogicError(
                    f"`$addUserReactions` — too many emojis found: `{len(emojis_to_add)}`. "
                    f"Maximum allowed is `{_REACTIONS_MAX}`."
                ))
                return

            target_msg: discord.Message = ctx.message
            added: int = 0

            for emoji in emojis_to_add:
                try:
                    await target_msg.add_reaction(emoji)
                    added += 1
                    await asyncio.sleep(0.35)
                except discord.HTTPException as e:
                    if e.status == 429:
                        retry = getattr(e, 'retry_after', 1.0)
                        await asyncio.sleep(retry)
                        try:
                            await target_msg.add_reaction(emoji)
                            added += 1
                        except Exception as e2:
                            ctx.log_event(f"تنبيه: فشل إضافة الإيموجي `{emoji}` بعد إعادة المحاولة: `{e2}`")
                            continue
                    elif e.status == 400:
                        ctx.log_event(f"تنبيه: تم تخطي إيموجي غير متاح أو غير مدعوم: `{emoji}`")
                        continue
                    else:
                        ctx.log_event(f"تنبيه: فشل إضافة الإيموجي `{emoji}`: `{e.text}`")
                        continue
                except discord.Forbidden:
                    await _send_error(ch, FDEnvironmentError(
                        "`$addUserReactions` — bot lacks `Add Reactions` permission in this channel"
                    ))
                    return
                except Exception as ex:
                    ctx.log_event(f"تنبيه: خطأ غير متوقع مع الإيموجي `{emoji}`: `{str(ex)}`")
                    continue

            ctx.log_event(f"addUserReactions → added {added} reaction(s) to user message")
            return

        # ── addBotReactions ───────────────────────────────────────────
        if name == "addBotReactions":
            if not args:
                await _send_error(ch, FDLogicError(
                    "`$addBotReactions` requires at least one emoji argument"
                ))
                return

            if ctx.last_bot_message is None:
                await _send_error(ch, FDEnvironmentError(
                    "`$addBotReactions` — no bot message was sent yet in this script execution"
                ))
                return

            # دمج واستخراج ذكي أيضاً لرسائل البوت
            resolved_text = "".join(ctx.resolve(arg) for arg in args)
            emojis_to_add = _extract_all_emojis(resolved_text)

            if not emojis_to_add:
                ctx.log_event("تنبيه: لم يتم العثور على أي إيموجيات صالحة في أمر $addBotReactions")
                return

            if len(emojis_to_add) > _REACTIONS_MAX:
                await _send_error(ch, FDLogicError(
                    f"`$addBotReactions` — too many emojis found: `{len(emojis_to_add)}`. "
                    f"Maximum allowed is `{_REACTIONS_MAX}`."
                ))
                return

            target_msg: discord.Message = ctx.last_bot_message
            added: int = 0

            for emoji in emojis_to_add:
                try:
                    await target_msg.add_reaction(emoji)
                    added += 1
                    await asyncio.sleep(0.35)
                except discord.HTTPException as e:
                    if e.status == 429:
                        retry = getattr(e, 'retry_after', 1.0)
                        await asyncio.sleep(retry)
                        try:
                            await target_msg.add_reaction(emoji)
                            added += 1
                        except Exception as e2:
                            ctx.log_event(f"تنبيه: فشل إضافة الإيموجي `{emoji}` بعد إعادة المحاولة: `{e2}`")
                            continue
                    elif e.status == 400:
                        ctx.log_event(f"تنبيه: تم تخطي إيموجي غير متاح أو غير مدعوم: `{emoji}`")
                        continue
                    else:
                        ctx.log_event(f"تنبيه: فشل إضافة الإيموجي `{emoji}`: `{e.text}`")
                        continue
                except discord.Forbidden:
                    await _send_error(ch, FDEnvironmentError(
                        "`$addBotReactions` — bot lacks `Add Reactions` permission in this channel"
                    ))
                    return
                except Exception as ex:
                    ctx.log_event(f"تنبيه: خطأ غير متوقع مع الإيموجي `{emoji}`: `{str(ex)}`")
                    continue

            ctx.log_event(f"addBotReactions → added {added} reaction(s) to bot message `{target_msg.id}`")
            return

        # ── clear ─────────────────────────────────────────────────────
        if name == "clear":
            if not args:
                limit: int = _CLEAR_DEFAULT
            else:
                raw_limit: str = args[0].strip()

                if not raw_limit.lstrip("-").isdigit():
                    await _send_error(ch, FDLogicError(
                        f"`$clear` — expected an integer between `1` and `{_CLEAR_MAX}`, "
                        f"got: `{raw_limit}`"
                    ))
                    return

                parsed: int = int(raw_limit)

                if parsed < 1:
                    await _send_error(ch, FDLogicError(
                        f"`$clear` — value must be at least `1`, got: `{parsed}`"
                    ))
                    return

                if parsed > _CLEAR_MAX:
                    await _send_error(ch, FDLogicError(
                        f"`$clear` — value `{parsed}` exceeds the maximum allowed (`{_CLEAR_MAX}`). "
                        f"Discord's bulk delete limit is 100 messages per request."
                    ))
                    return

                limit = parsed

            try:
                deleted: list[discord.Message] = await ch.purge(limit=limit)
                ctx.log_event(f"clear [{limit}] → deleted {len(deleted)} message(s)")
            except discord.Forbidden:
                ctx.log_event("clear → ✗ no permission")
                await _send_error(ch, FDEnvironmentError(
                    "`$clear` — bot lacks `Manage Messages` permission in this channel"
                ))
            except discord.HTTPException as e:
                ctx.log_event(f"clear → ✗ HTTP error: {e.status}")
                await _send_error(ch, FDRuntimeError(
                    f"`$clear` — Discord API error: `{e.text}`"
                ))
            return

        # ── var ──────────────────────────────────────────────────────
        if name == "var":
            if len(args) == 2:
                ctx.set_var(args[0], args[1])
                ctx.log_event(f"var [{args[0]}] ← {_truncate(args[1])!r}")
            elif len(args) != 1:
                await _send_error(ch, FDLogicError(
                    "`$var` accepts one argument (read) or two arguments (define)"
                ))
            return

        # ── setVar ───────────────────────────────────────────────────
        if name == "setVar":
            if len(args) == 2:
                data = _load_data()
                data[args[0]] = args[1]
                _save_data(data)
                ctx.log_event(f"setVar [{args[0]}] ← {_truncate(args[1])!r} (persistent)")
            else:
                await _send_error(ch, FDLogicError(
                    "`$setVar` requires two arguments: $setVar[name; value]"
                ))
            return

        # ── getVar ───────────────────────────────────────────────────
        if name == "getVar":
            if args:
                data = _load_data()
                value = str(data.get(args[0], ""))
                ctx.log_event(f"getVar [{args[0]}] → {_truncate(value)!r}")
            return

        # ── sendMessage ──────────────────────────────────────────────
        if name == "sendMessage":
            if len(args) == 1:
                ctx.stop_typing()
                sent: discord.Message = await ch.send(args[0])
                ctx.last_bot_message = sent
                ctx.log_event(f"sendMessage → {_truncate(args[0])!r}")
            else:
                await _send_error(ch, FDLogicError(
                    "`$sendMessage` requires one argument: $sendMessage[text]"
                ))
            return

        # ── title ─────────────────────────────────────────────────────
        if name == "title":
            if len(args) == 1:
                ctx.embed_builder.title = args[0]
                ctx.log_event(f"title → {_truncate(args[0])!r}")
            else:
                await _send_error(ch, FDLogicError(
                    "`$title` requires one argument: $title[text]"
                ))
            return

        # ── description ───────────────────────────────────────────────
        if name == "description":
            if len(args) == 1:
                ctx.embed_builder.description = args[0]
                ctx.log_event(f"description → {_truncate(args[0])!r}")
            else:
                await _send_error(ch, FDLogicError(
                    "`$description` requires one argument: $description[text]"
                ))
            return

        # ── color ─────────────────────────────────────────────────────
        if name == "color":
            if len(args) == 1:
                ctx.embed_builder.color = _parse_color(args[0])
                ctx.log_event(f"color → {args[0]!r}")
            else:
                await _send_error(ch, FDLogicError(
                    "`$color` requires one argument: $color[hex or name]\n"
                    f"Named colors: {', '.join(sorted(_NAMED_COLORS))}"
                ))
            return

        # ── footer ────────────────────────────────────────────────────
        if name == "footer":
            if len(args) == 1:
                ctx.embed_builder.footer = args[0]
                ctx.log_event(f"footer → {_truncate(args[0])!r}")
            else:
                await _send_error(ch, FDLogicError(
                    "`$footer` requires one argument: $footer[text]"
                ))
            return

        # ── sendEmbedMessage ──────────────────────────────────────────
        if name == "sendEmbedMessage":
            if len(args) < 5 or not args[4].strip():
                await _send_error(ch, FDLogicError(
                    "`$sendEmbedMessage` requires 5 mandatory arguments:\n"
                    "`$sendEmbedMessage[channelID; title; description; color; footer]`"
                ))
                return

            ch_id_str = args[0].strip()
            try:
                ch_id = int(ch_id_str)
            except ValueError:
                await _send_error(ch, FDLogicError(
                    f"`$sendEmbedMessage` — invalid channel ID: `{ch_id_str}`"
                ))
                return

            target_ch = ctx.bot.get_channel(ch_id)
            if not target_ch:
                await _send_error(ch, FDEnvironmentError(
                    f"`$sendEmbedMessage` — channel `{ch_id_str}` not found or bot has no access"
                ))
                return

            embed = discord.Embed(
                title=args[1],
                description=args[2],
                color=_parse_color(args[3]),
            )
            embed.set_footer(text=args[4])
            if args[4].strip():
                embed.set_footer(text=args[4])

            try:
                ctx.stop_typing()
                sent: discord.Message = await target_ch.send(embed=embed)
                ctx.last_bot_message = sent
                ctx.log_event(
                    f"sendEmbedMessage [{_truncate(args[1])}] → sent to channel {ch_id_str}"
                )
            except discord.Forbidden:
                await _send_error(ch, FDEnvironmentError(
                    f"`$sendEmbedMessage` — bot lacks permission to send in channel `{ch_id_str}`"
                ))
            except discord.HTTPException as e:
                await _send_error(ch, FDRuntimeError(
                    f"`$sendEmbedMessage` — failed to send: `{e.text}`"
                ))
            return

        # ── strictArgs ───────────────────────────────────────────────
        if name == "strictArgs":
            if len(args) == 2:
                constraint = args[0].strip()

                m = re.match(r'^(>=|<=|!=|>|<|=)(\d+)$', constraint)
                if not m:
                    await _send_error(ch, FDLogicError(
                        f"`$strictArgs` — invalid comparison format: `{constraint}`\n"
                        f"Valid examples: `>2` `=3` `<5` `>=1` `<=4` `!=0`"
                    ))
                    return

                op  = m.group(1)
                num = int(m.group(2))

                words      = ctx.message.content.strip().split()
                word_count = max(0, len(words) - 1)

                ok = {
                    ">":  word_count >  num,
                    "<":  word_count <  num,
                    "=":  word_count == num,
                    ">=": word_count >= num,
                    "<=": word_count <= num,
                    "!=": word_count != num,
                }[op]

                ctx.log_event(f"strictArgs [{constraint}] → {'✓' if ok else '✗'} ({word_count} words)")

                if not ok:
                    ctx.stop_typing()
                    await ch.send(args[1])
            else:
                await _send_error(ch, FDLogicError(
                    "`$strictArgs` requires two arguments: $strictArgs[comparison; error_message]\n"
                    "Example: `$strictArgs[>2; Please provide more than 2 words]`"
                ))
            return

        # ── randomint ────────────────────────────────────────────────
        if name == "randomint":
            if len(args) == 2:
                try:
                    a, b = int(float(args[0])), int(float(args[1]))
                    result = random.randint(min(a, b), max(a, b))
                    ctx.stop_typing()
                    dest = await ctx.get_dest()
                    await dest.send(str(result))
                    ctx.log_event(f"randomint [{min(a,b)}..{max(a,b)}] → {result}")
                except Exception:
                    await _send_error(ch, FDRuntimeError(
                        "`$randomint` expects numbers: $randomint[min; max]"
                    ))
            else:
                await _send_error(ch, FDLogicError(
                    "`$randomint` requires two arguments: $randomint[min; max]"
                ))
            return

        # ── randomstr ────────────────────────────────────────────────
        if name == "randomstr":
            if args:
                chosen = random.choice(args)
                ctx.stop_typing()
                dest = await ctx.get_dest()
                await dest.send(chosen)
                ctx.log_event(f"randomstr [{len(args)} options] → {_truncate(chosen)!r}")
            else:
                await _send_error(ch, FDLogicError(
                    "`$randomstr` requires at least one string"
                ))
            return

        # ── randomUserID ─────────────────────────────────────────────
        if name == "randomUserID":
            guild = ctx.message.guild
            if not guild:
                await _send_error(ch, FDEnvironmentError(
                    "`$randomUserID` only works inside servers"
                ))
                return
            members = [m for m in guild.members if not m.bot]
            if not members:
                await _send_error(ch, FDEnvironmentError(
                    "No human members found in this server"
                ))
                return
            chosen_member = random.choice(members)
            ctx.stop_typing()
            dest = await ctx.get_dest()
            await dest.send(str(chosen_member.id))
            ctx.log_event(f"randomUserID → {chosen_member.id}")
            return

        # ── addTimestamp ──────────────────────────────────────────────
        if name == "addTimestamp":
            now = int(time.time())
            ts = f'<t:{now}:T>'
            ctx.stop_typing()
            dest = await ctx.get_dest()
            await dest.send(ts)
            ctx.log_event(f"addTimestamp → {ts}")
            return

        # ── and / or (not usable as standalone commands) ──────────────
        if name in ("and", "or"):
            await _send_error(ch, FDLogicError(
                f"`${name}` can only be used inside a condition — example: `$if[$and[x == 1; y == 2]]`"
            ))
            return

        # ── uptime ───────────────────────────────────────────────────
        if name == "uptime":
            if _BOT_START_TIME == 0.0:
                await _send_error(ch, FDEnvironmentError(
                    "`$uptime` — bot start time was never set. "
                    "Make sure `set_bot_start_time()` is called in `on_ready`."
                ))
                return
            elapsed = time.time() - _BOT_START_TIME
            uptime_str = _format_uptime(elapsed)
            ctx.stop_typing()
            dest = await ctx.get_dest()
            await dest.send(uptime_str)
            ctx.log_event(f"uptime → {uptime_str}")
            return

        # ── return ────────────────────────────────────────────────────
        if name == "return":
            if not args:
                await _send_error(ch, FDLogicError(
                    "`$return` requires one argument: `$return[var]`"
                ))
                return
            key = args[0].strip()
            if not key:
                await _send_error(ch, FDLogicError(
                    "`$return[]` — variable name cannot be empty"
                ))
                return
            if key not in ctx.return_vars:
                await _send_error(ch, FDRuntimeError(
                    f"`$return[{key}]` — `{key}` has no value stored by any `$returnXxx` command"
                ))
                return
            ctx.stop_typing()
            dest = await ctx.get_dest()
            sent: discord.Message = await dest.send(str(ctx.return_vars[key]))
            ctx.last_bot_message = sent
            ctx.log_event(f"return [{key}] → {_truncate(str(ctx.return_vars[key]))!r}")
            return

        # ── returnGetReactions ───────────────────────────────────────
        if name == "returnGetReactions":
            if len(args) != 6:
                await _send_error(ch, FDLogicError(
                    "`$returnGetReactions` requires 6 arguments:\n"
                    "`$returnGetReactions[channelID; messageID; type; var; separator; emoji]`"
                ))
                return

            ch_id_str = args[0].strip()
            msg_id_str = args[1].strip()
            type_str = args[2].strip().lower()
            var_name = args[3].strip()
            separator = _parse_separator(args[4])
            emoji_raw = args[5].strip()

            if not ch_id_str.isdigit() or not msg_id_str.isdigit():
                await _send_error(ch, FDLogicError(
                    "`$returnGetReactions` — channelID and messageID must be integers"
                ))
                return

            if type_str not in ("usersid", "tr"):
                await _send_error(ch, FDLogicError(
                    f"`$returnGetReactions` — unknown type `{type_str}`.\n"
                    f"Valid types are: `usersID` or `tr(total-reactions)`."
                ))
                return

            if not var_name:
                await _send_error(ch, FDLogicError(
                    "`$returnGetReactions` — variable name cannot be empty"
                ))
                return

            ch_id = int(ch_id_str)
            msg_id = int(msg_id_str)

            target_ch = ctx.bot.get_channel(ch_id)
            if not target_ch:
                await _send_error(ch, FDEnvironmentError(
                    f"`$returnGetReactions` — channel `{ch_id_str}` not found or bot has no access"
                ))
                return

            try:
                target_msg = await target_ch.fetch_message(msg_id)
            except discord.NotFound:
                await _send_error(ch, FDEnvironmentError(
                    f"`$returnGetReactions` — message `{msg_id_str}` not found in channel `{ch_id_str}`"
                ))
                return
            except discord.Forbidden:
                await _send_error(ch, FDEnvironmentError(
                    "`$returnGetReactions` — bot lacks `Read Message History` permission in that channel"
                ))
                return
            except discord.HTTPException as e:
                await _send_error(ch, FDRuntimeError(
                    f"`$returnGetReactions` — failed to fetch message: `{e.text}`"
                ))
                return

            matched_reaction: discord.Reaction | None = None
            for reaction in target_msg.reactions:
                r_emoji = str(reaction.emoji)
                if r_emoji == emoji_raw:
                    matched_reaction = reaction
                    break
                if hasattr(reaction.emoji, 'name') and reaction.emoji.name == emoji_raw:
                    matched_reaction = reaction
                    break

            if matched_reaction is None:
                if type_str == "tr":
                    ctx.return_vars[var_name] = "0"
                    ctx.log_event(f"returnGetReactions [{emoji_raw}] → 0 reactions stored in `{var_name}`")
                    return
                else:
                    await _send_error(ch, FDRuntimeError(
                        f"`$returnGetReactions` — emoji `{emoji_raw}` was not found on message `{msg_id_str}`"
                    ))
                    return

            try:
                users = [u async for u in matched_reaction.users() if not u.bot]
            except discord.HTTPException as e:
                await _send_error(ch, FDRuntimeError(
                    f"`$returnGetReactions` — failed to fetch reaction users: `{e.text}`"
                ))
                return

            if type_str == "tr":
                result = str(len(users))
            else: # usersID
                if not users:
                    await _send_error(ch, FDRuntimeError(
                        f"`$returnGetReactions` — no human users reacted with `{emoji_raw}` on message `{msg_id_str}`"
                    ))
                    return
                result = separator.join(str(u.id) for u in users)

            ctx.return_vars[var_name] = result
            ctx.log_event(f"returnGetReactions [{emoji_raw} ({type_str})] → stored in `{var_name}`")
            return

        # ── returnGuildUsersID ────────────────────────────────────────
        if name == "returnGuildUsersID":
            if len(args) != 4:
                await _send_error(ch, FDLogicError(
                    "`$returnGuildUsersID` requires 4 arguments:\n"
                    "`$returnGuildUsersID[guildID; cache/chunk; var; separator]`"
                ))
                return

            guild_id_str = args[0].strip()
            fetch_mode   = args[1].strip().lower()
            var_name     = args[2].strip()
            separator    = _parse_separator(args[3])

            if not guild_id_str or not guild_id_str.isdigit():
                await _send_error(ch, FDLogicError(
                    f"`$returnGuildUsersID` — invalid guild ID: `{guild_id_str}`"
                ))
                return

            if fetch_mode not in ("cache", "chunk"):
                await _send_error(ch, FDLogicError(
                    f"`$returnGuildUsersID` — fetch mode must be `cache` or `chunk`, "
                    f"got: `{fetch_mode}`"
                ))
                return

            if not var_name:
                await _send_error(ch, FDLogicError(
                    "`$returnGuildUsersID` — variable name cannot be empty"
                ))
                return

            guild = ctx.bot.get_guild(int(guild_id_str))
            if not guild:
                await _send_error(ch, FDEnvironmentError(
                    f"`$returnGuildUsersID` — guild `{guild_id_str}` not found "
                    f"or bot is not in it"
                ))
                return

            if fetch_mode == "chunk":
                try:
                    await guild.chunk()
                except discord.HTTPException as e:
                    await _send_error(ch, FDRuntimeError(
                        f"`$returnGuildUsersID` — failed to chunk guild: `{e.text}`"
                    ))
                    return

            members = [m for m in guild.members if not m.bot]
            if not members:
                await _send_error(ch, FDRuntimeError(
                    f"`$returnGuildUsersID` — no human members found in guild `{guild_id_str}`"
                ))
                return

            ctx.return_vars[var_name] = separator.join(str(m.id) for m in members)
            ctx.log_event(
                f"returnGuildUsersID [{fetch_mode}] → {len(members)} member(s) "
                f"stored in `{var_name}`"
            )
            return

        # ── returnGuildChannelsID ─────────────────────────────────────
        if name == "returnGuildChannelsID":
            if len(args) != 4:
                await _send_error(ch, FDLogicError(
                    "`$returnGuildChannelsID` requires 4 arguments:\n"
                    "`$returnGuildChannelsID[GuildID; ChannelType; var; separator]`\n"
                    f"Channel types: {', '.join(k for k in _CHANNEL_TYPES)}"
                ))
                return

            guild_id_str = args[0].strip()
            ch_type_raw  = args[1].strip().lower() or "all"
            var_name     = args[2].strip()
            separator    = _parse_separator(args[3])

            if not guild_id_str or not guild_id_str.isdigit():
                await _send_error(ch, FDLogicError(
                    f"`$returnGuildChannelsID` — invalid guild ID: `{guild_id_str}`"
                ))
                return

            if ch_type_raw not in _CHANNEL_TYPES:
                await _send_error(ch, FDLogicError(
                    f"`$returnGuildChannelsID` — unknown channel type: `{ch_type_raw}`\n"
                    f"Valid types: {', '.join(_CHANNEL_TYPES)}"
                ))
                return

            if not var_name:
                await _send_error(ch, FDLogicError(
                    "`$returnGuildChannelsID` — variable name cannot be empty"
                ))
                return

            guild = ctx.bot.get_guild(int(guild_id_str))
            if not guild:
                await _send_error(ch, FDEnvironmentError(
                    f"`$returnGuildChannelsID` — guild `{guild_id_str}` not found "
                    f"or bot is not in it"
                ))
                return

            type_filter = _CHANNEL_TYPES[ch_type_raw]
            if type_filter is None:
                channels = guild.channels
            else:
                channels = [c for c in guild.channels if isinstance(c, type_filter)]

            if not channels:
                await _send_error(ch, FDRuntimeError(
                    f"`$returnGuildChannelsID` — no `{ch_type_raw}` channels found "
                    f"in guild `{guild_id_str}`"
                ))
                return

            ctx.return_vars[var_name] = separator.join(str(c.id) for c in channels)
            ctx.log_event(
                f"returnGuildChannelsID [{ch_type_raw}] → {len(channels)} channel(s) "
                f"stored in `{var_name}`"
            )
            return

        # ── returnGuildRolesID ────────────────────────────────────────
        if name == "returnGuildRolesID":
            if len(args) != 4:
                await _send_error(ch, FDLogicError(
                    "`$returnGuildRolesID` requires 4 arguments:\n"
                    "`$returnGuildRolesID[GuildID; permission; var; separator]`\n"
                    "Leave permission empty or use `all` to get all roles.\n"
                    f"Named permissions: {', '.join(sorted(_PERMISSION_NAMES))}"
                ))
                return

            guild_id_str = args[0].strip()
            perm_raw     = args[1].strip()
            var_name     = args[2].strip()
            separator    = _parse_separator(args[3])

            if not guild_id_str or not guild_id_str.isdigit():
                await _send_error(ch, FDLogicError(
                    f"`$returnGuildRolesID` — invalid guild ID: `{guild_id_str}`"
                ))
                return

            if not var_name:
                await _send_error(ch, FDLogicError(
                    "`$returnGuildRolesID` — variable name cannot be empty"
                ))
                return

            perm_filter = _resolve_permission(perm_raw)
            if perm_filter is False:
                await _send_error(ch, FDLogicError(
                    f"`$returnGuildRolesID` — unknown permission: `{perm_raw}`\n"
                    f"Use a permission name, a permission value (integer), "
                    f"or leave empty / `all` for all roles.\n"
                    f"Named permissions: {', '.join(sorted(_PERMISSION_NAMES))}"
                ))
                return

            guild = ctx.bot.get_guild(int(guild_id_str))
            if not guild:
                await _send_error(ch, FDEnvironmentError(
                    f"`$returnGuildRolesID` — guild `{guild_id_str}` not found "
                    f"or bot is not in it"
                ))
                return

            if perm_filter is None:
                roles = [r for r in guild.roles if r.name != "@everyone"]
            else:
                roles = [
                    r for r in guild.roles
                    if r.name != "@everyone"
                    and r.permissions >= perm_filter
                ]

            if not roles:
                await _send_error(ch, FDRuntimeError(
                    f"`$returnGuildRolesID` — no roles found matching "
                    f"permission `{perm_raw or 'all'}` in guild `{guild_id_str}`"
                ))
                return

            ctx.return_vars[var_name] = separator.join(str(r.id) for r in roles)
            ctx.log_event(
                f"returnGuildRolesID [{perm_raw or 'all'}] → {len(roles)} role(s) "
                f"stored in `{var_name}`"
            )
            return

        # ── ping ─────────────────────────────────────────────────────
        if name == "ping":
            latency_ms = round(ctx.bot.latency * 1000)
            ctx.stop_typing()
            dest = await ctx.get_dest()
            await dest.send(f"{latency_ms}ms")
            ctx.log_event(f"ping → {latency_ms}ms")
            return

        # ── deletecommand ─────────────────────────────────────────────
        if name == "deletecommand":
            try:
                await ctx.message.delete()
                ctx.log_event("deletecommand → deleted")
            except discord.Forbidden:
                ctx.log_event("deletecommand → ✗ no permission")
                await _send_error(ch, FDEnvironmentError(
                    "`$deletecommand` — bot lacks permission to delete messages in this channel"
                ))
            except discord.NotFound:
                ctx.log_event("deletecommand → ✗ message not found")
            return

        # ── log ───────────────────────────────────────────────────────
        if name == "log":
            channel_id_str = args[0].strip() if args else ""
            name_code      = args[1].strip() if len(args) > 1 else ""

            if not channel_id_str:
                await _send_error(ch, FDLogicError(
                    "`$log` requires at least a channel ID: "
                    "`$log[channelID]` or `$log[channelID; name_code]`"
                ))
                return

            try:
                channel_id = int(channel_id_str)
            except ValueError:
                await _send_error(ch, FDLogicError(
                    f"`$log` — invalid channel ID: `{channel_id_str}`"
                ))
                return

            ctx.snapshot_log(channel_id, name_code)
            ctx.log_event(
                f"log [{name_code or 'unnamed'}] → snapshot taken "
                f"({len(ctx._pending_logs[-1].entries)} event(s)), "
                f"will send to channel {channel_id}"
            )
            return

        # ── dm ────────────────────────────────────────────────────────
        if name == "dm":
            if not args:
                ctx.dm_target = ctx.message.author
                ctx.log_event(f"dm → target set to author ({ctx.message.author.id})")
                return

            target_str = args[0].strip()
            if not target_str:
                await _send_error(ch, FDLogicError(
                    "`$dm[]` — target cannot be empty. "
                    "Use `$dm` (no brackets) to DM the command author."
                ))
                return

            target_user = await _resolve_dm_target(target_str, ctx, ch)
            if target_user is None:
                return

            ctx.dm_target = target_user
            ctx.log_event(f"dm → target set to {target_user} ({target_user.id})")
            return

        if name in ("message", "messageID", "authorID", "username"):
            return

        await _send_error(ch, FDSyntaxError(f"Unknown command `{name}`"))

    # ------ Condition evaluator ------
    def _evaluate(self, expr: str, ctx: ExecutionContext) -> bool:
        expr = ctx.resolve(expr).strip()

        and_match = re.match(r'^\$and\[(.+)\]$', expr, re.DOTALL)
        if and_match:
            return all(self._evaluate(c, ctx) for c in _split_args(and_match.group(1)))

        or_match = re.match(r'^\$or\[(.+)\]$', expr, re.DOTALL)
        if or_match:
            return any(self._evaluate(c, ctx) for c in _split_args(or_match.group(1)))

        for op in ("==", "!=", ">=", "<=", ">", "<"):
            if op in expr:
                left, right = map(str.strip, expr.split(op, 1))
                try:
                    l_num, r_num = float(left), float(right)
                    if op == "==": return l_num == r_num
                    if op == "!=": return l_num != r_num
                    if op == ">":  return l_num >  r_num
                    if op == "<":  return l_num <  r_num
                    if op == ">=": return l_num >= r_num
                    if op == "<=": return l_num <= r_num
                except ValueError:
                    if op == "==": return left == right
                    if op == "!=": return left != right

        return False


# ─────────────────────────────────────────────
# Color InputCode(Soon...)
# ─────────────────────────────────────────────

def get_reserved_names() -> set[str]:
    return KNOWN_COMMANDS


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

async def run_script(message: discord.Message, bot: discord.Client, script_text: str):
    interpreter = Interpreter(script_text)
    ctx = ExecutionContext(message, bot)
    await interpreter.run(ctx)