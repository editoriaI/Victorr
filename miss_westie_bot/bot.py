"""Entry point for the Miss Westie Discord bot."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Iterable

import discord
from discord.ext import commands
from dotenv import load_dotenv

from .config import Settings, load_settings
from .db import Database
from .cogs import DEFAULT_COGS
from .utils import configure_logging


class MissWestieBot(commands.Bot):
    """Discord bot tailored for the Miss Westie community."""

    def __init__(self, settings: Settings):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=settings.bot.prefix,
            description=settings.bot.description,
            intents=intents,
            help_command=None,
        )

        self.settings = settings
        self.db = Database(settings.database.path)
        self.log = logging.getLogger("miss_westie.bot")

    async def setup_hook(self) -> None:
        self.log.info("Initialising database")
        await self.db.initialize()

        await self._load_cogs(DEFAULT_COGS)

        if self.settings.bot.sync_commands_on_start:
            synced = await self.tree.sync()
            self.log.info("Synced %s application commands", len(synced))

        activity_type = getattr(discord.ActivityType, self.settings.bot.status_type, discord.ActivityType.listening)
        await self.change_presence(activity=discord.Activity(type=activity_type, name=self.settings.bot.activity))
        self.log.info("Startup complete")

    async def _load_cogs(self, cogs: Iterable[str]) -> None:
        for cog in cogs:
            module_name = f"miss_westie_bot.cogs.{cog}"
            self.log.debug("Loading cog %s", module_name)
            await self.load_extension(module_name)

    async def close(self) -> None:
        await super().close()
        await self.db.close()


async def create_bot() -> MissWestieBot:
    """Initialise settings and create a bot instance."""

    load_dotenv()
    settings = load_settings()
    configure_logging()
    return MissWestieBot(settings)


async def _runner() -> None:
    bot = await create_bot()
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is not set in the environment")
    async with bot:
        await bot.start(token)


def run() -> None:
    """Entrypoint that runs the bot until it is stopped."""

    asyncio.run(_runner())


__all__ = ["MissWestieBot", "run", "create_bot"]

if __name__ == "__main__":
    run()
