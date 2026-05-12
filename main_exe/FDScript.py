# FDScript.py - FDScript Interpreter for Discord Bots
import discord
import json
import os
import re

# ─────────────────────────────────────────────
# Persistent storage
# ─────────────────────────────────────────────
DATA_FILE = "data.json"

def _load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_data(data: dict):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class StopExecution(Exception):
    """لإيقاف تنفيذ السكربت (مثل strictArgs)"""
    pass


# ─────────────────────────────────────────────
# Execution Context
# ─────────────────────────────────────────────
class ExecutionContext:
    def __init__(self, message: discord.Message, bot: discord.Client):
        self.message = message
        self.bot = bot
        self.temp_vars: dict = {}

        self.builtins: dict = {
            "authorID":      str(message.author.id),
            "authorName":    message.author.name,
            "channelID":     str(message.channel.id),
            "channelName":   message.channel.name,
            "guildName":     message.guild.name if message.guild else "DM",
            "mention":       message.author.mention,
            "botName":       bot.user.name if bot.user else "",
            "botID":         str(bot.user.id) if bot.user else "",
        }

    def get_var(self, name: str) -> str:
        name = name.strip()
        if name in self.temp_vars:
            return str(self.temp_vars[name])
        if name in self.builtins:
            return str(self.builtins[name])
        return ""

    def set_var(self, name: str, value: str):
        self.temp_vars[name.strip()] = value

    def resolve(self, text: str) -> str:
        if not text:
            return text

        # $var[name]
        def _replace_var(m):
            return self.get_var(m.group(1))
        text = re.sub(r'\$var\[([^\[\]]+)\]', _replace_var, text)

        # $getVar[name]
        def _replace_getvar(m):
            data = _load_data()
            return str(data.get(m.group(1).strip(), ""))
        text = re.sub(r'\$getVar\[([^\[\]]+)\]', _replace_getvar, text)

        # Math Operations
        def _replace_math(m):
            try:
                op = m.group(1)
                args = [x.strip() for x in m.group(2).split(";")]
                nums = [float(self.resolve(arg)) for arg in args]

                if op == "sum" and len(nums) == 2:
                    result = nums[0] + nums[1]
                elif op == "sub" and len(nums) == 2:
                    result = nums[0] - nums[1]
                elif op == "mul" and len(nums) == 2:
                    result = nums[0] * nums[1]
                elif op == "div" and len(nums) == 2:
                    if nums[1] == 0:
                        return "❌ خطأ: قسمة على صفر"
                    result = nums[0] / nums[1]
                elif op == "mod" and len(nums) == 2:
                    result = nums[0] % nums[1]
                else:
                    return "❌ خطأ في العملية"
                return str(int(result)) if result.is_integer() else str(result)
            except Exception:
                return "❌ خطأ حسابي"

        text = re.sub(r'\$(sum|sub|mul|div|mod)\[([^\[\]]+)\]', _replace_math, text)

        # $message → النص بعد الأمر فقط
        full_content = self.message.content.strip()
        parts = full_content.split(None, 1)
        text = text.replace("$message", parts[1] if len(parts) > 1 else "")

        # Builtins
        for key, val in self.builtins.items():
            text = text.replace(f"${key}", str(val))

        return text


# ─────────────────────────────────────────────
# Lexer
# ─────────────────────────────────────────────
class Command:
    def __init__(self, name: str, args: list[str], raw: str):
        self.name = name
        self.args = args
        self.raw = raw


KNOWN_COMMANDS = {
    "if", "elif", "else", "endif",
    "while", "endwhile", "for", "endfor", "break",
    "var", "setVar", "getVar", "sendMessage", "embed", "strictArgs",
    "sum", "sub", "mul", "div", "mod",
}


def tokenise(line: str) -> Command | str | None:
    line = line.strip()
    if not line or line.startswith(("#", "//")):
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
    if not rest.endswith("]"):
        raise SyntaxError(f"خطأ في إغلاق القوس في الأمر {name}")

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
# ─────────────────────────────────────────────
# Interpreter (نسخة محسنة - دعم تداخل أفضل)
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# Interpreter (نسخة محسنة - دعم break/loops)
# ─────────────────────────────────────────────
class Interpreter:
    def __init__(self, script: str):
        self.source_lines = script.splitlines()

    async def run(self, ctx: ExecutionContext):
        tokens = []
        for line in self.source_lines:
            try:
                tok = tokenise(line)
                if isinstance(tok, Command) and tok.name == "__unknown__":
                    await ctx.message.channel.send(f"❌ أمر غير معروف: {tok.args[0]}")
                    return
                if tok is not None:
                    tokens.append(tok)
            except SyntaxError as e:
                await ctx.message.channel.send(f"❌ خطأ في السكربت: {str(e)}")
                return

        try:
            await self._execute(tokens, ctx, 0)
        except StopExecution:
            pass

    async def _execute(self, tokens: list, ctx: ExecutionContext, start: int = 0):
        i = start
        while i < len(tokens):
            tok = tokens[i]

            if isinstance(tok, str):
                await ctx.message.channel.send(ctx.resolve(tok))
                i += 1
                continue

            if tok.name == "break":
                return "BREAK"

            if tok.name == "if":
                res = await self._exec_if(tokens, i, ctx)
                if res == "BREAK":
                    return "BREAK"
                i = res
                continue

            if tok.name == "while":
                res = await self._exec_while(tokens, i, ctx)
                if res == "BREAK":
                    return "BREAK"
                i = res
                continue

            if tok.name == "for":
                res = await self._exec_for(tokens, i, ctx)
                if res == "BREAK":
                    return "BREAK"
                i = res
                continue

            if tok.name in ("endif", "endwhile", "endfor", "elif", "else"):
                return i

            await self._exec_command(tok, ctx)
            i += 1
        return i

    # ====================== Improved Functions ======================
    async def _exec_if(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        i = start + 1
        branch_taken = False
        while i < len(tokens):
            tok = tokens[i]
            if tok.name in ("if", "elif"):
                cond_val = self._evaluate(tok.args[0] if tok.args else "", ctx)
                i += 1
                execute = not branch_taken and cond_val
                if execute:
                    branch_taken = True
                res = await self._run_block_until(tokens, i, {"elif", "else", "endif"}, ctx, execute)
                if res == "BREAK":
                    return "BREAK"
                i = res
                continue
            if tok.name == "else":
                i += 1
                res = await self._run_block_until(tokens, i, {"endif"}, ctx, not branch_taken)
                if res == "BREAK":
                    return "BREAK"
                i = res
                continue
            if tok.name == "endif":
                return i + 1
            i += 1
        return i

    async def _exec_while(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        tok = tokens[start]
        cond_str = tok.args[0] if tok.args else ""
        body_start = start + 1
        body_end = self._find_closer(tokens, body_start, "while", "endwhile")

        while self._evaluate(cond_str, ctx):
            result = await self._run_block_slice(tokens, body_start, body_end, ctx)
            if result == "BREAK":
                return body_end + 1
        return body_end + 1

    async def _exec_for(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        tok = tokens[start]
        count_str = ctx.resolve(tok.args[0] if tok.args else "0")
        try:
            count = int(count_str)
        except:
            count = 0
        body_start = start + 1
        body_end = self._find_closer(tokens, body_start, "for", "endfor")

        for _ in range(count):
            result = await self._run_block_slice(tokens, body_start, body_end, ctx)
            if result == "BREAK":
                return body_end + 1
        return body_end + 1

    async def _run_block_until(self, tokens, start, stoppers, ctx, execute):
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
                    await ctx.message.channel.send(ctx.resolve(tok))
                elif tok.name == "break":
                    return "BREAK"
                elif tok.name == "if":
                    res = await self._exec_if(tokens, i, ctx)
                    if res == "BREAK":
                        return "BREAK"
                    i = res
                    continue
                elif tok.name == "while":
                    res = await self._exec_while(tokens, i, ctx)
                    if res == "BREAK":
                        return "BREAK"
                    i = res
                    continue
                elif tok.name == "for":
                    res = await self._exec_for(tokens, i, ctx)
                    if res == "BREAK":
                        return "BREAK"
                    i = res
                    continue
                else:
                    await self._exec_command(tok, ctx)
            i += 1
        return i

    async def _run_block_slice(self, tokens, start, end, ctx):
        i = start
        while i < end:
            tok = tokens[i]
            if isinstance(tok, str):
                await ctx.message.channel.send(ctx.resolve(tok))
            elif tok.name == "break":
                return "BREAK"
            elif tok.name == "if":
                res = await self._exec_if(tokens, i, ctx)
                if res == "BREAK":
                    return "BREAK"
                i = res
                continue
            elif tok.name == "while":
                res = await self._exec_while(tokens, i, ctx)
                if res == "BREAK":
                    return "BREAK"
                i = res
                continue
            elif tok.name == "for":
                res = await self._exec_for(tokens, i, ctx)
                if res == "BREAK":
                    return "BREAK"
                i = res
                continue
            else:
                await self._exec_command(tok, ctx)
            i += 1
        return None

    def _find_closer(self, tokens, start, opener, closer):
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
        return len(tokens) - 1

# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────
async def run_script(message: discord.Message, bot: discord.Client, script_text: str):
    interpreter = Interpreter(script_text)
    ctx = ExecutionContext(message, bot)
    await interpreter.run(ctx)