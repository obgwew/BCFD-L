# cmds_FDScripts/sum.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, FDRuntimeError, _send_error


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) != 2:
        await _send_error(ch, FDLogicError("`$sum` requires 2 arguments: `$sum[a; b]`"))
        return
    try:
        a, b = float(args[0].strip()), float(args[1].strip())
    except ValueError:
        await _send_error(ch, FDRuntimeError(f"`$sum` — non-numeric arguments: `{args[0].strip()}`, `{args[1].strip()}`"))
        return
    res = a + b
    value = str(int(res)) if res == int(res) else str(res)
    ctx.stop_typing()
    dest = await ctx.get_dest()
    sent = await dest.send(value)
    ctx.last_bot_message = sent
    ctx.log_event(f"sum [{a} + {b}] → {value}")