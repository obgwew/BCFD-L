# FDScript.py — Interpreter & Public API
# ─────────────────────────────────────────────────────────────

import importlib
import re
import io
import sys
import discord

sys.modules.setdefault('FDScript', sys.modules[__name__])

from .FDCore import (
    set_vars_dir,
    set_bot_start_time,
    get_reserved_names,
    ExecutionContext,
    Command,
    tokenise_line,
    _split_args,
    _send_error,
    _truncate,
    _parse_separator,
    _resolve_dm_target,
    _resolve_permission,
    _CHANNEL_TYPES,
    _PERMISSION_NAMES,
    _REACTIONS_MAX,
    _extract_all_emojis,
    _LOG_CHAR_LIMIT,
    _LOG_FILE_LIMIT,
    _parse_color,
    _NAMED_COLORS,
    _CLEAR_DEFAULT,
    _CLEAR_MAX,
    _load_data,
    _save_data,
    _BOT_START_TIME,
    _format_uptime,
    _cooldowns,  
    FDSyntaxError,
    FDLogicError,
    FDRuntimeError,
    FDEnvironmentError,
    FDAbortScript,
    register_inline_resolver,
)


# ─────────────────────────────────────────────
# Command Registry and
# ─────────────────────────────────────────────

def _load_cmd(name: str):
    package_name = __package__ or ''
    try:
        if package_name:
            return importlib.import_module(f".cmds_FDScripts.{name}", package=package_name)
        return importlib.import_module(f"cmds_FDScripts.{name}")
    except ModuleNotFoundError:
        return None


def _resolve_inline_cmd(cmd_name: str, args: list, ctx) -> 'str | None':
    module = _load_cmd(cmd_name)
    if module and hasattr(module, 'resolve_inline'):
        return module.resolve_inline(args, ctx)
    return None

register_inline_resolver(_resolve_inline_cmd)


# ─────────────────────────────────────────────
# Global Condition Evaluator
# ─────────────────────────────────────────────

def evaluate_condition(expr: str, ctx: ExecutionContext) -> bool:
    expr = ctx.resolve(expr).strip()

    if expr.lower() == "true": return True
    if expr.lower() == "false": return False

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
# Interpreter
# ─────────────────────────────────────────────

class Interpreter:
    def __init__(self, script: str):
        self.source_lines = script.splitlines()

    # ── Main entry point ──────────────────────────────────────
    async def run(self, ctx: ExecutionContext):
        tokens = self._tokenise_all()
        errors = self._validate(tokens)
        
        ctx.is_global_reply = any(
            isinstance(t, Command) and t.name == "reply" and not t.args 
            for t in tokens
        )

        if errors:
            ch = getattr(ctx.message, 'channel', None)
            if ch is not None:
                lines = "\n".join(f"{e._icon} **{e._category}** — {e.msg}" for e in errors)
                await ch.send(f"**{'One error' if len(errors) == 1 else f'{len(errors)} errors'} found, aborted:**\n{lines}")
            else:
                for e in errors: print(f"[Error] {e._category}: {e.msg}")
            return
        
        try:
            await self._execute(tokens, ctx)
        except FDAbortScript:
            ctx.log_event("script execution aborted.")

        await self._flush_embed(ctx)
        await self._flush_logs(ctx)

    # ── Flush embed builder ───────────────────────────────────
    async def _flush_embed(self, ctx: ExecutionContext):
        if not ctx.embed_builder.is_set():
            return
        ch = ctx.message.channel
        ctx.stop_typing()
        
        if getattr(ctx, "is_global_reply", False):
            sent = await ctx.message.reply(embed=ctx.embed_builder.build())
        else:
            sent = await ch.send(embed=ctx.embed_builder.build())
            
        ctx.last_bot_message = sent
        ctx.log_event("embed builder → sent")

    # ── Flush pending log snapshots ───────────────────────────
    async def _flush_logs(self, ctx: ExecutionContext):
        ch = ctx.message.channel
        for pending in ctx._pending_logs:
            target_ch = ctx.bot.get_channel(pending.channel_id)
            if not target_ch:
                await _send_error(ch, FDEnvironmentError(f"`$log` — channel `{pending.channel_id}` not found or bot has no access"))
                continue

            label     = f"[FDScript Log{f' — {pending.name_code}' if pending.name_code else ''}]"
            body      = "\n".join(pending.entries) if pending.entries else "(no events in this range)"
            full_text = f"{label}\n{body}"
            block     = f"```\n{full_text}\n```"

            if len(block) <= _LOG_CHAR_LIMIT:
                await target_ch.send(block)
            else:
                raw_bytes = full_text.encode("utf-8")
                if len(raw_bytes) > _LOG_FILE_LIMIT:
                    await _send_error(ch, FDRuntimeError("`$log` — log snapshot exceeds the 10 MB file limit"))
                    continue
                safe_name = ''.join(c if c.isalnum() or c in ('-', '_') else '_' for c in pending.name_code).strip('_') or "fdscript_log"
                await target_ch.send("📄 Log snapshot too large for a code block — sent as file:", file=discord.File(fp=io.BytesIO(raw_bytes), filename=f"{safe_name}.txt"))

    # ── Join multi-line commands before tokenising ────────────
    def _join_multiline(self) -> list[str]:
        joined: list[str] = []
        buffer: list[str] = []
        depth = 0

        for line in self.source_lines:
            for i, ch in enumerate(line):
                if ch == '[': depth += 1
                elif ch == ']': depth -= 1
                elif ch == '#' and depth == 0: break 

            buffer.append(line)

            if depth <= 0:
                joined.append('\n'.join(buffer))
                buffer = []
                depth = 0

        if buffer: joined.append('\n'.join(buffer))
        return joined

    # ── Tokenise all lines upfront ────────────────────────────
    def _tokenise_all(self) -> list:
        result = []
        for line in self._join_multiline():
            try:
                toks = tokenise_line(line)
                result.extend(toks)
            except SyntaxError as e:
                result.append(Command("__syntax_error__", [str(e)], line))
        return result

    # ── Validate — returns list[_FDError] ─────────────────────
    def _validate(self, tokens: list) -> list:
        errors, stack = [], []
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
            if isinstance(tok, str): continue

            if tok.name in OPENERS:
                stack.append((tok.name, line_num))
                continue

            if tok.name in CLOSERS:
                expected = CLOSERS[tok.name]
                if not stack: errors.append(FDSyntaxError(f"Line {line_num}: `${tok.name}` without `${expected}`"))
                elif stack[-1][0] != expected: errors.append(FDLogicError(f"Line {line_num}: `${tok.name}` does not match `${stack[-1][0]}`"))
                else: stack.pop()
                continue

            if tok.name == "break":
                if not any(t[0] in ("while", "for") for t in stack): errors.append(FDLogicError(f"Line {line_num}: `$break` outside loops"))
                continue

            if tok.name == "log" and (not tok.args or not tok.args[0].strip()):
                errors.append(FDLogicError(f"Line {line_num}: `$log` requires at least a channel ID"))
                continue

            if tok.name == "dm" and tok.args and not any(a.strip() for a in tok.args):
                errors.append(FDLogicError(f"Line {line_num}: `$dm[]` — target cannot be empty."))
                continue

        for opener, line_num in stack:
            errors.append(FDSyntaxError(f"Line {line_num}: `${opener}` not closed with `${OPENERS[opener]}`"))
        return errors

    # ── Execute ───────────────────────────────────────────────
    async def _execute(self, tokens: list, ctx: ExecutionContext, start: int = 0) -> int:
        i = start
        while i < len(tokens):
            tok = tokens[i]
            i += 1

            if isinstance(tok, str):
                ctx.stop_typing()
                dest = await ctx.get_dest()
                resolved_text = ctx.resolve(tok)
                if getattr(ctx, "is_global_reply", False):
                    sent = await ctx.message.reply(resolved_text)
                else:
                    sent = await dest.send(resolved_text)
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

    # ── if / elif / else / endif ──────────────────────────────
    async def _exec_if(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        i, branch_taken = start, False

        while i < len(tokens):
            tok = tokens[i]
            if tok.name in ("if", "elif"):
                cond_str = tok.args[0] if tok.args else ""
                cond_val = self._evaluate(cond_str, ctx)
                ctx.log_event(f"{tok.name} [{cond_str}] → {'✓' if cond_val else '✗'}")
                i += 1
                execute = not branch_taken and cond_val
                if execute: branch_taken = True
                i = await self._run_block_until(tokens, i, {"elif", "else", "endif"}, ctx, execute=execute)
                if i == "break": return "break"
                continue

            if tok.name == "else":
                ctx.log_event(f"else → {'taken' if not branch_taken else 'skipped'}")
                i += 1
                i = await self._run_block_until(tokens, i, {"endif"}, ctx, execute=not branch_taken)
                if i == "break": return "break"
                continue

            if tok.name == "endif": return i + 1
            i += 1
        return i

    # ── while / endwhile ──────────────────────────────────────
    async def _exec_while(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        tok = tokens[start]
        cond_str = tok.args[0] if tok.args else ""
        body_start, body_end = start + 1, self._find_closer(tokens, start + 1, "while", "endwhile")
        iterations = 0
        while self._evaluate(cond_str, ctx):
            iterations += 1
            if await self._run_block_slice(tokens, body_start, body_end, ctx) == "break": break
        ctx.log_event(f"while [{cond_str}] → {iterations} iters")
        return body_end + 1

    # ── for / endfor ──────────────────────────────────────────
    async def _exec_for(self, tokens: list, start: int, ctx: ExecutionContext) -> int:
        count_str = ctx.resolve(tokens[start].args[0]) if tokens[start].args else "0"
        try: count = int(count_str)
        except ValueError:
            await _send_error(ctx.message.channel, FDRuntimeError(f"`$for` expects integer, got: `{count_str}`"))
            count = 0
        body_start, body_end = start + 1, self._find_closer(tokens, start + 1, "for", "endfor")
        for _ in range(count):
            if await self._run_block_slice(tokens, body_start, body_end, ctx) == "break": break
        ctx.log_event(f"for [{count}] → {count} iters")
        return body_end + 1

    # ── _run_block_until ──────────────────────────────────────
    async def _run_block_until(self, tokens, start, stoppers, ctx, execute):
        i, depth = start, 0
        while i < len(tokens):
            tok = tokens[i]

            if not isinstance(tok, str):
                if depth > 0:
                    if tok.name in ("if", "while", "for"): depth += 1
                    elif tok.name in ("endif", "endwhile", "endfor"): depth -= 1
                    i += 1
                    continue

                if tok.name in stoppers: return i

                if not execute:
                    if tok.name in ("if", "while", "for"): depth = 1
                    i += 1
                    continue

                if tok.name == "break": return "break"
                if tok.name == "if":
                    i = await self._exec_if(tokens, i, ctx)
                    if i == "break": return "break"
                    continue
                if tok.name == "while":
                    i = await self._exec_while(tokens, i, ctx)
                    continue
                if tok.name == "for":
                    i = await self._exec_for(tokens, i, ctx)
                    continue

                await self._exec_command(tok, ctx)
                i += 1
                continue

            if execute and depth == 0:
                ctx.stop_typing()
                dest = await ctx.get_dest()
                resolved_text = ctx.resolve(tok)
                
                if getattr(ctx, "is_global_reply", False):
                    sent = await ctx.message.reply(resolved_text)
                else:
                    sent = await dest.send(resolved_text)
                ctx.last_bot_message = sent
            i += 1
        return i

    # ── _run_block_slice ──────────────────────────────────────
    async def _run_block_slice(self, tokens, start, end, ctx):
        i = start
        while i < end:
            tok = tokens[i]
            i += 1
            if isinstance(tok, str):
                ctx.stop_typing()
                dest = await ctx.get_dest()
                resolved_text = ctx.resolve(tok)
                if getattr(ctx, "is_global_reply", False):
                    sent = await ctx.message.reply(resolved_text)
                else:
                    sent = await dest.send(resolved_text)
                ctx.last_bot_message = sent
                continue
            if tok.name == "break": return "break"
            if tok.name == "if":
                res = await self._exec_if(tokens, i - 1, ctx)
                if res == "break": return "break"
                i = res
            elif tok.name == "while": i = await self._exec_while(tokens, i - 1, ctx)
            elif tok.name == "for": i = await self._exec_for(tokens, i - 1, ctx)
            else: await self._exec_command(tok, ctx)
        return None

    # ── _find_closer ──────────────────────────────────────────
    def _find_closer(self, tokens, start, opener, closer):
        depth, i = 0, start
        while i < len(tokens):
            tok = tokens[i]
            if not isinstance(tok, str):
                if tok.name == opener: depth += 1
                elif tok.name == closer:
                    if depth == 0: return i
                    depth -= 1
            i += 1
        return i

    # ── Execute a single command ──────────────────────────────
    async def _exec_command(self, cmd: Command, ctx: ExecutionContext):
        name = cmd.name
        args = [ctx.resolve(a) for a in cmd.args]
        ch   = ctx.message.channel

        if name in ("message", "messageID", "authorID", "username"): return

        module = _load_cmd(name)
        if module and hasattr(module, "execute"):
            await module.execute(cmd, args, ctx, ch)
            return

        await _send_error(ch, FDSyntaxError(f"Unknown command `{name}`"))

    # ── Condition evaluator ───────────────────────────────────
    def _evaluate(self, expr: str, ctx: ExecutionContext) -> bool:
        return evaluate_condition(expr, ctx)


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

async def run_script(message: discord.Message, bot: discord.Client, script_text: str, is_event: bool = False, is_reply: bool = False):
    interpreter = Interpreter(script_text)
    ctx = ExecutionContext(message, bot, is_event=is_event)
    if is_reply:
        ctx.is_global_reply = True
    await interpreter.run(ctx)