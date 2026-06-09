# cmds_FDScripts/footer.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error, _truncate


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 1:
        ctx.embed_builder.footer = args[0]
        ctx.log_event(f"footer → {_truncate(args[0])!r}")
    else:
        await _send_error(ch, FDLogicError("`$footer` requires one argument: $footer[text]"))