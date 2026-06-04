# cmds_FDScripts/endwhile_.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error


async def execute(
    cmd: Command,
    args: list[str],
    ctx: ExecutionContext,
    ch: discord.abc.Messageable,
) -> None:
    await _send_error(ch, FDLogicError(
        "`$endwhile` without a matching `$while`"
    ))