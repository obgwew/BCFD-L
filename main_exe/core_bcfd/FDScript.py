# FDScript.py - FDScript Interpreter for Discord Bots
import discord
import json
import os
import re
import random

# ─────────────────────────────────────────────
# Persistent storage
# ─────────────────────────────────────────────

_VARS_DIR: str = ''  

def set_vars_dir(path: str):
    global _VARS_DIR
    _VARS_DIR = path


def _load_data() -> dict:
    """يقرأ جميع ملفات bot_vars/ ويجمعها في dict واحد"""
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
    """يكتب كل متغير كملف منفصل — نفس بنية variables_view"""
    if not _VARS_DIR:
        return
    os.makedirs(_VARS_DIR, exist_ok=True)
    for name, value in data.items():
        safe  = ''.join(c for c in name if c.isalnum() or c in ('-', '_')).strip() or 'var'
        path  = os.path.join(_VARS_DIR, f'{safe}.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'name': name, 'value': str(value)},
                      f, ensure_ascii=False, indent=2)

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
            "authorID":   str(message.author.id),
            "authorName": message.author.name,
            "channelID":  str(message.channel.id),
            "channelName": message.channel.name,
            "guildName":  message.guild.name if message.guild else "DM",
            "mention":    message.author.mention,
            "botName":    bot.user.name if bot.user else "",
            "botID":      str(bot.user.id) if bot.user else "",
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

        # ── Random Operations ────────────────────────────────────────

        # $randomint[min; max]
        def _replace_randomint(m):
            parts = [x.strip() for x in m.group(1).split(";")]
            if len(parts) == 2:
                try:
                    a = int(float(self.resolve(parts[0])))
                    b = int(float(self.resolve(parts[1])))
                    return str(random.randint(min(a, b), max(a, b)))
                except Exception:
                    return "❌ خطأ في randomint"
            return "❌ خطأ في randomint – يجب: $randomint[min; max]"
        text = re.sub(r'\$randomint\[([^\[\]]+)\]', _replace_randomint, text)

        # $randomstr[txt1; txt2; txt3...]
        def _replace_randomstr(m):
            parts = [x.strip() for x in m.group(1).split(";")]
            parts = [p for p in parts if p]  # حذف العناصر الفارغة
            return random.choice(parts) if parts else ""
        text = re.sub(r'\$randomstr\[([^\[\]]+)\]', _replace_randomstr, text)

        # $randomUserID — يختار عضو عشوائي (غير بوت) من الخادم
        if "$randomUserID" in text:
            guild = self.message.guild
            picked = ""
            if guild:
                members = [m for m in guild.members if not m.bot]
                if members:
                    picked = str(random.choice(members).id)
            text = text.replace("$randomUserID", picked)

        # ─────────────────────────────────────────────────────────────

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
    # ── أوامر جديدة ──
    "randomint", "randomstr", "randomUserID",
    "and", "or",
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

    # ── فحص توازن الأقواس ────────────────────────────────────────
    depth = 0
    for ch in rest:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if depth < 0:
            raise SyntaxError(f"قوس زائد في الأمر: {name}")
    if depth != 0:
        raise SyntaxError(f"قوس غير مغلق في الأمر: {name}")
    # ─────────────────────────────────────────────────────────────

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

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------
    async def run(self, ctx: ExecutionContext):
        tokens = self._tokenise_all()
        errors = self._validate(tokens)
        if errors:
            await ctx.message.channel.send(
                "❌ **يوجد أخطاء في السكربت، لم يتم التنفيذ:**\n" + "\n".join(errors)
            )
            return
        await self._execute(tokens, ctx)

    # ------------------------------------------------------------------
    # Tokenise every line upfront — errors stored as tokens, not raised
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Validate all tokens before execution — returns list of errors
    # ------------------------------------------------------------------
    def _validate(self, tokens: list) -> list[str]:
        errors = []
        stack  = []  # (opener_name, line_num)

        OPENERS = {"if": "endif", "while": "endwhile", "for": "endfor"}
        CLOSERS = {"endif": "if", "endwhile": "while", "endfor": "for"}

        for i, tok in enumerate(tokens):
            line_num = i + 1

            if isinstance(tok, Command) and tok.name == "__syntax_error__":
                errors.append(f"• سطر {line_num}: {tok.args[0]}")
                continue

            if isinstance(tok, Command) and tok.name == "__unknown__":
                errors.append(f"• سطر {line_num}: لا يوجد أمر اسمه `{tok.args[0]}`")
                continue

            if isinstance(tok, str):
                continue

            if tok.name in OPENERS:
                stack.append((tok.name, line_num))
                continue

            if tok.name in CLOSERS:
                expected = CLOSERS[tok.name]
                if not stack:
                    errors.append(f"• سطر {line_num}: `${tok.name}` بدون `${expected}`")
                elif stack[-1][0] != expected:
                    errors.append(
                        f"• سطر {line_num}: `${tok.name}` لا يطابق "
                        f"`${stack[-1][0]}` المفتوح في سطر {stack[-1][1]}"
                    )
                    stack.pop()
                else:
                    stack.pop()
                continue

            if tok.name == "break":
                in_loop = any(t[0] in ("while", "for") for t in stack)
                if not in_loop:
                    errors.append(f"• سطر {line_num}: `$break` خارج `$while` أو `$for`")
                continue

        for opener, line_num in stack:
            errors.append(f"• سطر {line_num}: `${opener}` لم يُغلق بـ `${OPENERS[opener]}`")

        return errors

    # ------------------------------------------------------------------
    # Execute a flat token list
    # ------------------------------------------------------------------
    async def _execute(self, tokens: list, ctx: ExecutionContext, start: int = 0) -> int:
        i = start
        while i < len(tokens):
            tok = tokens[i]
            i += 1

            if isinstance(tok, str):
                await ctx.message.channel.send(ctx.resolve(tok))
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

    # ------------------------------------------------------------------
    # if / elif / else / endif
    # ------------------------------------------------------------------
    async def _exec_if(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        i = start
        branch_taken = False

        while i < len(tokens):
            tok = tokens[i]

            if tok.name in ("if", "elif"):
                cond_str = tok.args[0] if tok.args else ""
                cond_val = self._evaluate(cond_str, ctx)
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

    # ------------------------------------------------------------------
    # while / endwhile
    # ------------------------------------------------------------------
    async def _exec_while(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        tok = tokens[start]
        cond_str = tok.args[0] if tok.args else ""
        body_start = start + 1
        body_end = self._find_closer(tokens, body_start, "while", "endwhile")

        while self._evaluate(cond_str, ctx):
            result = await self._run_block_slice(tokens, body_start, body_end, ctx)
            if result == "break":
                break

        return body_end + 1

    # ------------------------------------------------------------------
    # for / endfor
    # ------------------------------------------------------------------
    async def _exec_for(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        tok = tokens[start]
        count_str = ctx.resolve(tok.args[0]) if tok.args else "0"

        try:
            count = int(count_str)
        except ValueError:
            await ctx.message.channel.send(
                "❌ خطأ في نوع الوسيط في الأمر for، يجب أن يكون رقماً صحيحاً"
            )
            count = 0

        body_start = start + 1
        body_end = self._find_closer(tokens, body_start, "for", "endfor")

        for _ in range(count):
            result = await self._run_block_slice(tokens, body_start, body_end, ctx)
            if result == "break":
                break

        return body_end + 1

    # ------------------------------------------------------------------
    # Run tokens until a stopper token is found
    # ------------------------------------------------------------------
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
                    await ctx.message.channel.send(ctx.resolve(tok))
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

    # ------------------------------------------------------------------
    # Run tokens[start:end] — used by while/for bodies
    # ------------------------------------------------------------------
    async def _run_block_slice(
        self, tokens: list, start: int, end: int, ctx: ExecutionContext
    ) -> str | None:
        i = start
        while i < end:
            tok = tokens[i]
            i += 1

            if isinstance(tok, str):
                await ctx.message.channel.send(ctx.resolve(tok))
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

    # ------------------------------------------------------------------
    # Find matching closer for a block (handles nesting)
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Execute a single non-block command
    # ------------------------------------------------------------------
    async def _exec_command(self, cmd: Command, ctx: ExecutionContext):
        name = cmd.name
        args = [ctx.resolve(a) for a in cmd.args]

        if name == "var":
            if len(args) == 2:
                ctx.set_var(args[0], args[1])
            elif len(args) == 1:
                pass
            else:
                await ctx.message.channel.send("❌ خطأ في عدد الوسيطات في الأمر var")
            return

        if name == "setVar":
            if len(args) == 2:
                data = _load_data()
                data[args[0]] = args[1]
                _save_data(data)
            else:
                await ctx.message.channel.send("❌ خطأ في عدد الوسيطات في الأمر setVar")
            return

        if name == "getVar":
            return

        if name == "sendMessage":
            if len(args) == 1:
                await ctx.message.channel.send(args[0])
            else:
                await ctx.message.channel.send(
                    "❌ خطأ في عدد الوسيطات في الأمر sendMessage"
                )
            return

        if name == "embed":
            if len(args) == 3:
                color_str = args[2].lstrip("#")
                try:
                    color_int = int(color_str, 16)
                except ValueError:
                    color_int = 0x2B2D31
                embed = discord.Embed(
                    title=args[0],
                    description=args[1],
                    color=color_int,
                )
                await ctx.message.channel.send(embed=embed)
            else:
                await ctx.message.channel.send(
                    "❌ خطأ في عدد الوسيطات في الأمر embed – يجب: $embed[title; desc; color]"
                )
            return

        if name == "strictArgs":
            if len(args) == 2:
                msg_content = ctx.message.content.strip()
                parts = msg_content.split(None, 1)
                actual_arg = parts[1].strip() if len(parts) > 1 else ""
                if not actual_arg:
                    await ctx.message.channel.send(args[1])
            else:
                await ctx.message.channel.send(
                    "❌ خطأ في عدد الوسيطات في الأمر strictArgs"
                )
            return

        # ── أوامر Random ─────────────────────────────────────────────

        if name == "randomint":
            if len(args) == 2:
                try:
                    a = int(float(args[0]))
                    b = int(float(args[1]))
                    await ctx.message.channel.send(str(random.randint(min(a, b), max(a, b))))
                except Exception:
                    await ctx.message.channel.send("❌ خطأ في randomint: الوسيطات يجب أن تكون أرقاماً")
            else:
                await ctx.message.channel.send(
                    "❌ خطأ في عدد الوسيطات في الأمر randomint – يجب: $randomint[min; max]"
                )
            return

        if name == "randomstr":
            if len(args) >= 1:
                await ctx.message.channel.send(random.choice(args))
            else:
                await ctx.message.channel.send("❌ خطأ في randomstr: يجب تحديد نص واحد على الأقل")
            return

        if name == "randomUserID":
            guild = ctx.message.guild
            if guild:
                members = [m for m in guild.members if not m.bot]
                if members:
                    await ctx.message.channel.send(str(random.choice(members).id))
                else:
                    await ctx.message.channel.send("❌ لا يوجد أعضاء في الخادم")
            else:
                await ctx.message.channel.send("❌ هذا الأمر يعمل فقط داخل الخوادم")
            return

        # ── $and و $or لا تُستخدم كأوامر مستقلة ────────────────────
        if name in ("and", "or"):
            await ctx.message.channel.send(
                f"❌ `${name}` تُستخدم فقط داخل شرط `$if` — مثال: `$if[$and[x == 1; y == 2]]`"
            )
            return

        # ─────────────────────────────────────────────────────────────

        if name in ("message", "authorID", "username"):
            return

        await ctx.message.channel.send(f"❌ لا يوجد أمر اسمه `{name}`")

    # ------------------------------------------------------------------
    # Condition evaluator
    # ------------------------------------------------------------------
    def _evaluate(self, expr: str, ctx: ExecutionContext) -> bool:
        expr = ctx.resolve(expr).strip()

        # ── $and[cond1; cond2; ...] — يجب أن تتحقق جميع الشروط ──────
        and_match = re.match(r'^\$and\[(.+)\]$', expr, re.DOTALL)
        if and_match:
            conditions = _split_args(and_match.group(1))
            return all(self._evaluate(c, ctx) for c in conditions)

        # ── $or[cond1; cond2; ...] — يكفي تحقق شرط واحد ──────────────
        or_match = re.match(r'^\$or\[(.+)\]$', expr, re.DOTALL)
        if or_match:
            conditions = _split_args(or_match.group(1))
            return any(self._evaluate(c, ctx) for c in conditions)

        # ─────────────────────────────────────────────────────────────

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
# Public API
# ─────────────────────────────────────────────

async def run_script(message: discord.Message, bot: discord.Client, script_text: str):
    interpreter = Interpreter(script_text)
    ctx = ExecutionContext(message, bot)
    await interpreter.run(ctx)