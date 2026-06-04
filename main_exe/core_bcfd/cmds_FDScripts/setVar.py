# cmds_FDScripts/setVar.py
import discord
from FDScript import (
    ExecutionContext, Command,
    FDLogicError, _send_error, _truncate,
    _load_data, _save_data,
)


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 2:
        data = _load_data()
        data[args[0]] = args[1]
        _save_data(data)
        ctx.log_event(f"setVar [{args[0]}] ← {_truncate(args[1])!r} (persistent)")
    else:
        await _send_error(ch, FDLogicError(
            "`$setVar` requires two arguments: $setVar[name; value]"
        ))