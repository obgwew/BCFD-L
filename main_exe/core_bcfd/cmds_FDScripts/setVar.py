# cmds_FDScripts/setVar.py
import discord
from main_exe.core_bcfd.FDCore import (
    ExecutionContext, Command,
    FDLogicError, FDRuntimeError,
    _send_error, _load_data, _save_data, _truncate,
)

def _fmt(err) -> str:
    return f"{err._icon} **{err._category}** — {err.msg}"

def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    return _fmt(FDLogicError("`$setVar` cannot be used inline — use it as a standalone command."))

async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) != 2:
        await _send_error(ch, FDLogicError(
            "`$setVar` requires two arguments: `$setVar[name; value]`"
        ))

    name  = args[0].strip()
    value = args[1]

    if not name:
        await _send_error(ch, FDLogicError(
            "`$setVar` — variable name cannot be empty."
        ))

    data = _load_data()

    if name not in data:
        await _send_error(ch, FDRuntimeError(
            f"`$setVar[{name}]` — variable `{name}` does not exist.\n"
            f"Tip: Create it first from the Variables tab in BCFD."
        ))

    data[name] = value
    _save_data(data)
    ctx.log_event(f"setVar [{name}] ← {_truncate(value)!r} (persistent)")