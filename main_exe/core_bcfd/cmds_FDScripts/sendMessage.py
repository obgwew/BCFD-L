# cmds_FDScripts/cmd_sendMessage.py
import discord
from FDScript import ExecutionContext, Command, FDLogicError, _send_error, _truncate


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) == 1:
        ctx.stop_typing()
        sent = await ch.send(args[0])
        ctx.last_bot_message = sent
        ctx.log_event(f"sendMessage → {_truncate(args[0])!r}")
    else:
        await _send_error(ch, FDLogicError(
            "`$sendMessage` requires one argument: $sendMessage[text]"
        ))