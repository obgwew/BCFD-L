# cmds_FDScripts/if_.py
import discord
from FDScript import (
    ExecutionContext, Command,
    _split_args,
)


# ── Condition evaluator (mirrors Interpreter._evaluate) ──────────────────────

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


# ── Block runner: executes tokens[start] until it hits one of `stoppers` ─────

async def _run_block_until(
    tokens: list,
    start: int,
    stoppers: set,
    ctx: ExecutionContext,
    execute: bool,
    exec_command_fn,      
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
                    i = await execute_block(tokens, i, ctx, exec_command_fn)
                    if i == "break":
                        return "break"
                    continue
                elif tok.name == "while":
                    from cmds_FDScripts import while_ as while_mod
                    i = await while_mod.execute_block(tokens, i, ctx, exec_command_fn)
                    continue
                elif tok.name == "for":
                    from cmds_FDScripts import for_ as for_mod
                    i = await for_mod.execute_block(tokens, i, ctx, exec_command_fn)
                    continue
                else:
                    await exec_command_fn(tok, ctx)
        i += 1

    return i


# ── Main entry: handle entire if/elif/else/endif chain ───────────────────────

async def execute_block(
    tokens: list,
    start: int,
    ctx: ExecutionContext,
    exec_command_fn,
) -> int:
    """
    Called with `start` pointing at the $if token.
    Returns the index after $endif.
    """
    i = start
    branch_taken = False

    while i < len(tokens):
        tok = tokens[i]

        if tok.name in ("if", "elif"):
            cond_str = tok.args[0] if tok.args else ""
            cond_val = _evaluate(cond_str, ctx)
            label = "if" if tok.name == "if" else "elif"
            ctx.log_event(f"{label} [{cond_str}] → {'✓' if cond_val else '✗'}")
            i += 1
            do_exec = not branch_taken and cond_val
            if do_exec:
                branch_taken = True
            i = await _run_block_until(
                tokens, i, {"elif", "else", "endif"}, ctx,
                execute=do_exec, exec_command_fn=exec_command_fn,
            )
            if i == "break":
                return "break"
            continue

        if tok.name == "else":
            ctx.log_event(f"else → {'taken' if not branch_taken else 'skipped'}")
            i += 1
            i = await _run_block_until(
                tokens, i, {"endif"}, ctx,
                execute=not branch_taken, exec_command_fn=exec_command_fn,
            )
            if i == "break":
                return "break"
            continue

        if tok.name == "endif":
            return i + 1

        i += 1

    return i


# ── Standalone execute() — called when $if appears as a top-level command ────

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