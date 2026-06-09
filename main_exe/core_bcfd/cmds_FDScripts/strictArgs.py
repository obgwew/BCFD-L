# cmds_FDScripts/strictArgs.py
import re
import discord
from main_exe.core_bcfd.FDScript import (
    ExecutionContext, Command,
    FDLogicError, FDAbortScript,
    _send_error,
)


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) != 2:
        await _send_error(ch, FDLogicError(
            "`$strictArgs` requires two arguments: `$strictArgs[comparison; error_message]`\n"
            "Example: `$strictArgs[>2; Please provide more than 2 words]`"
        ))

    constraint = args[0].strip()
    error_msg  = args[1].strip()

    m = re.match(r'^(>|<|!)?(\d+)$', constraint)
    if not m:
        await _send_error(ch, FDLogicError(
            f"`$strictArgs` — invalid format: `{constraint}`\n"
            f"Valid examples: `2` `>2` `<2` `!2`"
        ))

    op  = m.group(1) or '='
    num = int(m.group(2))

    words      = ctx.message.content.strip().split()
    word_count = len(words) if ctx.is_event else max(0, len(words))

    ok = {
        '>': word_count >  num,
        '<': word_count <  num,
        '=': word_count == num,
        '!': word_count != num,
    }[op]

    ctx.log_event(f"strictArgs [{constraint}] → {'✓' if ok else '✗'} ({word_count} words)")

    if not ok:
        ctx.stop_typing()
        dest = await ctx.get_dest()
        if error_msg:
            sent = await dest.send(error_msg)
            ctx.last_bot_message = sent
        else:
            await dest.send("❌ Invalid arguments.")
        ctx.log_event(f"strictArgs [{constraint}] → Failed. Aborting script execution.")
        raise FDAbortScript()