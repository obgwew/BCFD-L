# cmds_FDScripts/image.py
import discord
from FDScript import (
    ExecutionContext, Command,
    FDLogicError, FDEnvironmentError, _send_error
)


def resolve_inline(args: list[str], ctx: ExecutionContext) -> str:
    """Allow $image[url] to be used inline — returns the URL as-is."""
    if not args:
        return ""
    return "".join(ctx.resolve(arg) for arg in args).strip()


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if not args:
        await _send_error(ch, FDLogicError(
            "`$image` requires an image URL argument — example: `$image[https://example.com/img.png]`"
        ))
        return

    resolved_url = "".join(ctx.resolve(arg) for arg in args).strip()

    if not resolved_url.startswith(("http://", "https://")):
        await _send_error(ch, FDLogicError(
            f"`$image` — invalid URL format: `{resolved_url}`. URL must start with http:// or https://"
        ))
        return

    ctx.stop_typing()
    dest = await ctx.get_dest()

    try:
        embed = discord.Embed()
        embed.set_image(url=resolved_url)

        sent = await dest.send(embed=embed)
        ctx.last_bot_message = sent
        ctx.log_event(f"image → sent image embed from URL")

    except discord.Forbidden:
        await _send_error(ch, FDEnvironmentError(
            "`$image` — bot lacks `Send Messages` or `Embed Links` permission in this channel."
        ))
    except discord.HTTPException as e:
        ctx.log_event(f"warning: failed to send image embed: `{e.text}`")