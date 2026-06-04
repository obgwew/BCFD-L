# cmds_FDScripts/break_.py

import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error

BREAK_SIGNAL = "break"


async def execute(
    cmd: Command,
    args: list[str],
    ctx: ExecutionContext,
    ch: discord.abc.Messageable,
) -> str:
    ctx.log_event("break → loop exited")
    return BREAK_SIGNAL