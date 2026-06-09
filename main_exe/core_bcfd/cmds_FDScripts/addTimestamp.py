# cmds_FDScripts/addTimestamp.py
import time
import discord
from FDScript import ExecutionContext, Command


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    ts = f'<t:{int(time.time())}:T>'
    ctx.stop_typing()
    dest = await ctx.get_dest()
    await dest.send(ts)
    ctx.log_event(f"addTimestamp → {ts}")