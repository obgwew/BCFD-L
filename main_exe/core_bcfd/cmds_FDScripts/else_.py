# cmds_FDScripts/else_.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error


async def execute(
    cmd: Command,
    args: list[str],
    ctx: ExecutionContext,
    ch: discord.abc.Messageable,
) -> None:
    await _send_error(ch, FDLogicError(
        "`$else` must be used inside a `$if` block — "
        "example:\n```\n$if[x == 1]\n  ...\n$else\n  ...\n$endif\n```"
    ))