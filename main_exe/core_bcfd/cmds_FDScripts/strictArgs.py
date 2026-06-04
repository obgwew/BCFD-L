# cmds_FDScripts/strictArgs.py
import re
import discord
from FDScript import (
    ExecutionContext, Command,
    FDLogicError,
    _send_error,
)


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) != 2:
        await _send_error(ch, FDLogicError(
            "`$strictArgs` requires two arguments: `$strictArgs[comparison; error_message]`\n"
            "Example: `$strictArgs[>2; Please provide more than 2 words]`"
        ))
        return

    constraint = args[0].strip()
    error_msg  = args[1]

    m = re.match(r'^(>=|<=|!=|>|<|=)(\d+)$', constraint)
    if not m:
        await _send_error(ch, FDLogicError(
            f"`$strictArgs` — invalid comparison format: `{constraint}`\n"
            f"Valid examples: `>2` `=3` `<5` `>=1` `<=4` `!=0`"
        ))
        return

    op  = m.group(1)
    num = int(m.group(2))

    words      = ctx.message.content.strip().split()
    word_count = max(0, len(words) - 1)

    ok = {
        ">":  word_count >  num,
        "<":  word_count <  num,
        "=":  word_count == num,
        ">=": word_count >= num,
        "<=": word_count <= num,
        "!=": word_count != num,
    }[op]

    ctx.log_event(f"strictArgs [{constraint}] → {'✓' if ok else '✗'} ({word_count} words)")

    if not ok:
        ctx.stop_typing()
        await ch.send(error_msg)