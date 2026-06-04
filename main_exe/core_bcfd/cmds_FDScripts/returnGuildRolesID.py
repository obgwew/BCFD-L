# cmds_FDScripts/returnGuildRolesID.py
import discord
from FDScript import (
    ExecutionContext, Command,
    FDLogicError, FDRuntimeError, FDEnvironmentError,
    _send_error, _parse_separator,
    _PERMISSION_NAMES, _resolve_permission,
)


async def execute(cmd: Command, args: list[str], ctx: ExecutionContext, ch: discord.abc.Messageable) -> None:
    if len(args) != 4:
        await _send_error(ch, FDLogicError(
            "`$returnGuildRolesID` requires 4 arguments:\n"
            "`$returnGuildRolesID[GuildID; permission; var; separator]`\n"
            "Leave permission empty or use `all` to get all roles.\n"
            f"Named permissions: {', '.join(sorted(_PERMISSION_NAMES))}"
        ))
        return

    guild_id_str = args[0].strip()
    perm_raw     = args[1].strip()
    var_name     = args[2].strip()
    separator    = _parse_separator(args[3])

    if not guild_id_str or not guild_id_str.isdigit():
        await _send_error(ch, FDLogicError(
            f"`$returnGuildRolesID` — invalid guild ID: `{guild_id_str}`"
        ))
        return

    if not var_name:
        await _send_error(ch, FDLogicError(
            "`$returnGuildRolesID` — variable name cannot be empty"
        ))
        return

    perm_filter = _resolve_permission(perm_raw)
    if perm_filter is False:
        await _send_error(ch, FDLogicError(
            f"`$returnGuildRolesID` — unknown permission: `{perm_raw}`\n"
            f"Use a permission name, a permission value (integer), "
            f"or leave empty / `all` for all roles.\n"
            f"Named permissions: {', '.join(sorted(_PERMISSION_NAMES))}"
        ))
        return

    guild = ctx.bot.get_guild(int(guild_id_str))
    if not guild:
        await _send_error(ch, FDEnvironmentError(
            f"`$returnGuildRolesID` — guild `{guild_id_str}` not found or bot is not in it"
        ))
        return

    if perm_filter is None:
        roles = [r for r in guild.roles if r.name != "@everyone"]
    else:
        roles = [
            r for r in guild.roles
            if r.name != "@everyone" and r.permissions >= perm_filter
        ]

    if not roles:
        await _send_error(ch, FDRuntimeError(
            f"`$returnGuildRolesID` — no roles found matching "
            f"permission `{perm_raw or 'all'}` in guild `{guild_id_str}`"
        ))
        return

    ctx.return_vars[var_name] = separator.join(str(r.id) for r in roles)
    ctx.log_event(
        f"returnGuildRolesID [{perm_raw or 'all'}] → {len(roles)} role(s) stored in `{var_name}`"
    )