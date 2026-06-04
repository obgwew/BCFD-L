# cmds_FDScripts/var.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error, _truncate


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 2:
        ctx.set_var(args[0], args[1])
        ctx.log_event(f"var [{args[0]}] ← {_truncate(args[1])!r}")

    elif len(args) == 1:
        value = ctx.get_var(args[0])
        ctx.stop_typing()
        dest = await ctx.get_dest()
        sent = await dest.send(value)
        ctx.last_bot_message = sent
        ctx.log_event(f"var [{args[0]}] → {_truncate(value)!r}")

    else:
        await _send_error(ch, FDLogicError(
            "`$var` accepts one argument (read+send) or two arguments (write)"
        ))