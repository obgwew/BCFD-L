# cmds_FDScripts/onlyIf.py
import discord
from FDScript import (
    ExecutionContext, Command,
    FDLogicError, FDAbortScript, _send_error, evaluate_condition
)

async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    resolved_args = [ctx.resolve(arg) for arg in args]

    if len(resolved_args) < 2:
        await _send_error(ch, FDLogicError(
            "`$onlyIf` requires a condition and an error message separated by a semicolon `;` — "
            "example: `$onlyIf[x == y; Custom Error Message!]`"
        ))
        return

    cond_str = resolved_args[0].strip()
    error_msg = resolved_args[1].strip()

    if not evaluate_condition(cond_str, ctx):
        ctx.stop_typing()
        dest = await ctx.get_dest()

        if error_msg:
            sent = await dest.send(error_msg)
            ctx.last_bot_message = sent

        ctx.log_event(f"onlyIf [{cond_str}] → Failed. Aborting script execution.")
        raise FDAbortScript()

    else:
        ctx.log_event(f"onlyIf [{cond_str}] → Passed. Continuing script.")