# cmds_FDScripts/while_.py
import discord
from FDScript import (
    ExecutionContext, Command,
    FDRuntimeError, _send_error,
    _split_args,
)


# ── Re-use the same evaluator as if_ ─────────────────────────────────────────

def _evaluate(expr: str, ctx: ExecutionContext) -> bool:
    import re
    expr = ctx.resolve(expr).strip()

    and_match = re.match(r'^\$and\[(.+)\]$', expr, re.DOTALL)
    if and_match:
        return all(_evaluate(c, ctx) for c in _split_args(and_match.group(1)))

    or_match = re.match(r'^\$or\[(.+)\]$', expr, re.DOTALL)
    if or_match:
        return any(_evaluate(c, ctx) for c in _split_args(or_match.group(1)))

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


# ── Find matching $endwhile ───────────────────────────────────────────────────

def _find_closer(tokens: list, start: int) -> int:
    depth = 0
    i = start
    while i < len(tokens):
        tok = tokens[i]
        if not isinstance(tok, str):
            if tok.name == "while":
                depth += 1
            elif tok.name == "endwhile":
                if depth == 0:
                    return i
                depth -= 1
        i += 1
    return i


# ── Run a slice of tokens (body of the loop) ─────────────────────────────────

async def _run_slice(
    tokens: list,
    start: int,
    end: int,
    ctx: ExecutionContext,
    exec_command_fn,
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
            from cmds_FDScripts import if_ as if_mod
            res = await if_mod.execute_block(tokens, i - 1, ctx, exec_command_fn)
            if res == "break":
                return "break"
            i = res
        elif tok.name == "while":
            i = await execute_block(tokens, i - 1, ctx, exec_command_fn)
        elif tok.name == "for":
            from cmds_FDScripts import for_ as for_mod
            i = await for_mod.execute_block(tokens, i - 1, ctx, exec_command_fn)
        else:
            await exec_command_fn(tok, ctx)

    return None


# ── Main block executor ───────────────────────────────────────────────────────

async def execute_block(
    tokens: list,
    start: int,
    ctx: ExecutionContext,
    exec_command_fn,
) -> int:
    """
    Called with `start` pointing at the $while token.
    Returns the index after $endwhile.
    """
    tok      = tokens[start]
    cond_str = tok.args[0] if tok.args else ""
    body_start = start + 1
    body_end   = _find_closer(tokens, body_start)

    iterations = 0
    while _evaluate(cond_str, ctx):
        iterations += 1
        result = await _run_slice(tokens, body_start, body_end, ctx, exec_command_fn)
        if result == "break":
            break

    ctx.log_event(f"while [{cond_str}] → {iterations} iter{'s' if iterations != 1 else ''}")
    return body_end + 1


# ── Standalone execute() ──────────────────────────────────────────────────────

async def execute(
    cmd: Command,
    args: list[str],
    ctx: ExecutionContext,
    ch: discord.abc.Messageable,
    *,
    tokens: list,
    token_index: int,
    exec_command_fn,
) -> int:
    return await execute_block(tokens, token_index, ctx, exec_command_fn)