# cmds_FDScripts/title.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error, _truncate


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 1:
        ctx.embed_builder.title = args[0]
        ctx.log_event(f"title → {_truncate(args[0])!r}")
    else:
        await _send_error(ch, FDLogicError("`$title` requires one argument: $title[text]"))