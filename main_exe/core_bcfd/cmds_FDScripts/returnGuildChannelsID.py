# cmds_FDScripts/returnGuildChannelsID.py
import discord
from FDScript import (
    ExecutionContext, Command,
    FDLogicError, FDRuntimeError, FDEnvironmentError,
    _send_error, _parse_separator,
    _CHANNEL_TYPES,
)


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) != 4:
        await _send_error(ch, FDLogicError(
            "`$returnGuildChannelsID` requires 4 arguments:\n"
            "`$returnGuildChannelsID[GuildID; ChannelType; var; separator]`\n"
            f"Channel types: {', '.join(_CHANNEL_TYPES)}"
        ))
        return

    guild_id_str = args[0].strip()
    ch_type_raw  = args[1].strip().lower() or "all"
    var_name     = args[2].strip()
    separator    = _parse_separator(args[3])

    if not guild_id_str or not guild_id_str.isdigit():
        await _send_error(ch, FDLogicError(
            f"`$returnGuildChannelsID` — invalid guild ID: `{guild_id_str}`"
        ))
        return

    if ch_type_raw not in _CHANNEL_TYPES:
        await _send_error(ch, FDLogicError(
            f"`$returnGuildChannelsID` — unknown channel type: `{ch_type_raw}`\n"
            f"Valid types: {', '.join(_CHANNEL_TYPES)}"
        ))
        return

    if not var_name:
        await _send_error(ch, FDLogicError(
            "`$returnGuildChannelsID` — variable name cannot be empty"
        ))
        return

    guild = ctx.bot.get_guild(int(guild_id_str))
    if not guild:
        await _send_error(ch, FDEnvironmentError(
            f"`$returnGuildChannelsID` — guild `{guild_id_str}` not found or bot is not in it"
        ))
        return

    type_filter = _CHANNEL_TYPES[ch_type_raw]
    channels = guild.channels if type_filter is None else [
        c for c in guild.channels if isinstance(c, type_filter)
    ]

    if not channels:
        await _send_error(ch, FDRuntimeError(
            f"`$returnGuildChannelsID` — no `{ch_type_raw}` channels found in guild `{guild_id_str}`"
        ))
        return

    ctx.return_vars[var_name] = separator.join(str(c.id) for c in channels)
    ctx.log_event(
        f"returnGuildChannelsID [{ch_type_raw}] → {len(channels)} channel(s) stored in `{var_name}`"
    )