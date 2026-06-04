# cmds_FDScripts/getVar.py
import discord
from FDScript import ExecutionContext, Command, _load_data, _truncate


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if args:
        data = _load_data()
        value = str(data.get(args[0], ""))
        ctx.log_event(f"getVar [{args[0]}] → {_truncate(value)!r}")