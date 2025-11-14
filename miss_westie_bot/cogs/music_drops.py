"""Music drop announcement utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from ..db import MusicDrop
from ..utils import require_staff_role


class MusicDrops(commands.Cog):
    """Allow staff to log and share new music drops."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="musicdrop", description="Log a new music drop for the community")
    @require_staff_role()
    async def musicdrop(
        self,
        ctx: commands.Context,
        title: str,
        artist: str,
        link: Optional[str] = None,
        release_date: Optional[str] = None,
    ) -> None:
        """Register a new music drop in the database."""

        drop = MusicDrop(
            title=title,
            artist=artist,
            link=link,
            release_date=release_date,
            submitted_by=ctx.author.id,
            created_at=datetime.utcnow(),
        )
        record_id = await self.bot.db.log_music_drop(drop)

        embed = discord.Embed(title="🎵 New Music Drop Logged", colour=discord.Colour.blurple())
        embed.add_field(name="Title", value=title, inline=False)
        embed.add_field(name="Artist", value=artist, inline=True)
        if release_date:
            embed.add_field(name="Release Date", value=release_date, inline=True)
        if link:
            embed.add_field(name="Link", value=link, inline=False)
        embed.set_footer(text=f"Recorded by {ctx.author.display_name} • Entry #{record_id}")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="musicdrops", description="Show the latest logged music drops")
    async def musicdrops(self, ctx: commands.Context, limit: Optional[int] = 5) -> None:
        """Display recently added music drops."""

        limit = max(1, min(limit or 5, 10))
        drops = await self.bot.db.recent_music_drops(limit)

        if not drops:
            await ctx.reply("No music drops recorded yet. Be the first to add one!", mention_author=False)
            return

        embed = discord.Embed(title="🎧 Latest Music Drops", colour=discord.Colour.pink())
        for drop in drops:
            description = f"**Artist:** {drop['artist']}\n"
            if drop.get("release_date"):
                description += f"**Release:** {drop['release_date']}\n"
            if drop.get("link"):
                description += f"[Listen here]({drop['link']})\n"
            embed.add_field(name=drop["title"], value=description, inline=False)

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MusicDrops(bot))
