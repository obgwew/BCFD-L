# cmds_FDScripts/elif_.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error


async def execute(
    cmd: Command,
    args: list[str],
    ctx: ExecutionContext,
    ch: discord.abc.Messageable,
) -> None:
    await _send_error(ch, FDLogicError(
        "`$elif` must be used inside a `$if` block — "
        "example:\n```\n$if[x == 1]\n  ...\n$elif[x == 2]\n  ...\n$endif\n```"
    ))