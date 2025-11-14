"""Custom command checks used across Miss Westie bot cogs."""

from __future__ import annotations

from typing import Iterable

import discord
from discord.ext import commands


def _has_any_role(member: discord.Member, roles: Iterable[str]) -> bool:
    role_names = {role.name for role in member.roles}
    return any(target in role_names for target in roles)


def _resolve_roles(ctx: commands.Context, roles: Iterable[str] | None, attribute: str) -> tuple[str, ...]:
    if roles:
        return tuple(roles)
    settings = getattr(ctx.bot, "settings", None)
    guild_settings = getattr(settings, "guild", None)
    if guild_settings is None:
        return tuple()
    return tuple(getattr(guild_settings, attribute, ()) or ())


def require_staff_role(roles: Iterable[str] | None = None) -> commands.CheckDecorator:
    """Restrict a command to members with a staff role."""

    async def predicate(ctx: commands.Context) -> bool:
        if not isinstance(ctx.author, discord.Member):  # pragma: no cover - type guard
            raise commands.CheckFailure("Command must be used in a guild context.")

        target_roles = _resolve_roles(ctx, roles, "staff_roles")
        if target_roles and _has_any_role(ctx.author, target_roles):
            return True

        if ctx.author.guild_permissions.manage_guild:
            return True

        raise commands.CheckFailure("You need a staff role to use this command.")

    return commands.check(predicate)


def require_verified_role(roles: Iterable[str] | None = None) -> commands.CheckDecorator:
    """Ensure the invoking member has one of the configured verified roles."""

    async def predicate(ctx: commands.Context) -> bool:
        if not isinstance(ctx.author, discord.Member):  # pragma: no cover - type guard
            raise commands.CheckFailure("Command must be used in a guild context.")

        target_roles = _resolve_roles(ctx, roles, "verified_roles")
        if target_roles and _has_any_role(ctx.author, target_roles):
            return True

        if ctx.author.guild_permissions.manage_guild:
            return True

        raise commands.CheckFailure("You need to be verified to use this command.")

    return commands.check(predicate)


__all__ = ["require_staff_role", "require_verified_role"]
