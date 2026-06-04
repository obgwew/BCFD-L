# cmds_FDScripts/for_.py
import discord
from FDScript import (
    ExecutionContext, Command,
    FDRuntimeError, _send_error,
)


# ── Find matching $endfor ─────────────────────────────────────────────────────

def _find_closer(tokens: list, start: int) -> int:
    depth = 0
    i = start
    while i < len(tokens):
        tok = tokens[i]
        if not isinstance(tok, str):
            if tok.name == "for":
                depth += 1
            elif tok.name == "endfor":
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
            from cmds_FDScripts import while_ as while_mod
            i = await while_mod.execute_block(tokens, i - 1, ctx, exec_command_fn)
        elif tok.name == "for":
            i = await execute_block(tokens, i - 1, ctx, exec_command_fn)
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
    tok        = tokens[start]
    count_str  = ctx.resolve(tok.args[0]) if tok.args else "0"

    try:
        count = int(count_str)
    except ValueError:
        ctx.log_event(f"for — invalid count `{count_str}`, skipping loop")
        body_start = start + 1
        body_end   = _find_closer(tokens, body_start)
        return body_end + 1

    body_start = start + 1
    body_end   = _find_closer(tokens, body_start)

    for _ in range(max(0, count)):
        result = await _run_slice(tokens, body_start, body_end, ctx, exec_command_fn)
        if result == "break":
            break

    ctx.log_event(f"for [{count}] → {count} iter{'s' if count != 1 else ''}")
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