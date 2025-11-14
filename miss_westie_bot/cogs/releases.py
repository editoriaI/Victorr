"""Release tracker commands."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from ..db import ReleaseAnnouncement
from ..utils import require_staff_role


class Releases(commands.Cog):
    """Track music releases for Miss Westie's community."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="release_add", description="Add a new release announcement")
    @require_staff_role()
    async def release_add(
        self,
        ctx: commands.Context,
        title: str,
        *,
        description: str,
        release_date: Optional[str] = None,
        link: Optional[str] = None,
    ) -> None:
        announcement = ReleaseAnnouncement(
            title=title,
            description=description,
            release_date=release_date,
            link=link,
            created_by=ctx.author.id,
            created_at=datetime.utcnow(),
        )
        release_id = await self.bot.db.create_release(announcement)

        embed = discord.Embed(title="🚀 New Release Incoming", colour=discord.Colour.magenta(), description=description)
        if release_date:
            embed.add_field(name="Release Date", value=release_date, inline=False)
        if link:
            embed.add_field(name="Listen", value=f"[Launch]({link})", inline=False)
        embed.set_footer(text=f"Recorded by {ctx.author.display_name} • Release #{release_id}")

        await ctx.reply(embed=embed, mention_author=False)

        guild_settings = getattr(getattr(self.bot, "settings", None), "guild", None)
        if guild_settings:
            for channel_id in guild_settings.announcement_channel_ids:
                channel = ctx.guild.get_channel(channel_id) if ctx.guild else None
                if channel:
                    await channel.send(embed=embed)

    @commands.hybrid_command(name="releases", description="Show upcoming releases")
    async def releases(self, ctx: commands.Context, limit: Optional[int] = 5) -> None:
        limit = max(1, min(limit or 5, 10))
        entries = await self.bot.db.recent_releases(limit)

        if not entries:
            await ctx.reply("No releases have been recorded yet.", mention_author=False)
            return

        embed = discord.Embed(title="🌸 Upcoming Releases", colour=discord.Colour.purple())
        for release in entries:
            value = release["description"]
            if release.get("release_date"):
                value = f"**Release Date:** {release['release_date']}\n{value}"
            if release.get("link"):
                value += f"\n[Listen]({release['link']})"
            embed.add_field(name=f"#{release['id']} — {release['title']}", value=value, inline=False)

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Releases(bot))
