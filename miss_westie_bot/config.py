"""Configuration helpers for the Miss Westie Discord bot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(slots=True)
class BotSettings:
    """Runtime configuration for the Discord bot instance."""

    prefix: str = "!"
    description: str = "Miss Westie's community assistant"
    activity: str = "serving Westie Nation"
    status_type: str = "listening"
    sync_commands_on_start: bool = True


@dataclass(slots=True)
class DatabaseSettings:
    """Settings that control the SQLite database connection."""

    path: str = "miss_westie.db"


@dataclass(slots=True)
class GuildSettings:
    """Server-specific settings used by moderation helpers."""

    staff_roles: tuple[str, ...] = field(default_factory=lambda: ("Admin", "Moderator"))
    verified_roles: tuple[str, ...] = field(default_factory=lambda: ("Verified",))
    announcement_channel_ids: tuple[int, ...] = field(default_factory=tuple)

    def with_staff_roles(self, roles: Iterable[str]) -> "GuildSettings":
        return GuildSettings(
            staff_roles=tuple(sorted({*roles})),
            verified_roles=self.verified_roles,
            announcement_channel_ids=self.announcement_channel_ids,
        )

    def with_verified_roles(self, roles: Iterable[str]) -> "GuildSettings":
        return GuildSettings(
            staff_roles=self.staff_roles,
            verified_roles=tuple(sorted({*roles})),
            announcement_channel_ids=self.announcement_channel_ids,
        )


@dataclass(slots=True)
class Settings:
    """Aggregate settings for the bot."""

    bot: BotSettings = field(default_factory=BotSettings)
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    guild: GuildSettings = field(default_factory=GuildSettings)


def _parse_role_list(value: str | None) -> tuple[str, ...]:
    if not value:
        return tuple()
    roles = [role.strip() for role in value.split(",") if role.strip()]
    return tuple(dict.fromkeys(roles))


def load_settings() -> Settings:
    """Create a :class:`Settings` instance using environment variables."""

    prefix = os.getenv("MISS_WESTIE_PREFIX", "!")
    description = os.getenv("MISS_WESTIE_DESCRIPTION", "Miss Westie's community assistant")
    activity = os.getenv("MISS_WESTIE_ACTIVITY", "serving Westie Nation")
    status_type = os.getenv("MISS_WESTIE_STATUS", "listening")
    sync_commands = os.getenv("MISS_WESTIE_SYNC_COMMANDS", "true").lower() == "true"

    db_path = os.getenv("MISS_WESTIE_DB", "miss_westie.db")

    staff_roles = _parse_role_list(os.getenv("MISS_WESTIE_STAFF_ROLES"))
    verified_roles = _parse_role_list(os.getenv("MISS_WESTIE_VERIFIED_ROLES"))
    announcement_channels_raw = os.getenv("MISS_WESTIE_ANNOUNCEMENT_CHANNELS", "")

    announcement_channels: list[int] = []
    for channel_id in announcement_channels_raw.split(","):
        channel_id = channel_id.strip()
        if not channel_id:
            continue
        try:
            announcement_channels.append(int(channel_id))
        except ValueError:
            continue

    settings = Settings(
        bot=BotSettings(
            prefix=prefix,
            description=description,
            activity=activity,
            status_type=status_type,
            sync_commands_on_start=sync_commands,
        ),
        database=DatabaseSettings(path=db_path),
    )

    guild_settings = settings.guild
    if staff_roles:
        guild_settings = guild_settings.with_staff_roles(staff_roles)
    if verified_roles:
        guild_settings = guild_settings.with_verified_roles(verified_roles)
    if announcement_channels:
        guild_settings = GuildSettings(
            staff_roles=guild_settings.staff_roles,
            verified_roles=guild_settings.verified_roles,
            announcement_channel_ids=tuple(announcement_channels),
        )

    return Settings(bot=settings.bot, database=settings.database, guild=guild_settings)


__all__ = [
    "BotSettings",
    "DatabaseSettings",
    "GuildSettings",
    "Settings",
    "load_settings",
]
