"""Collaboration finder commands."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from ..db import CollabOpportunity
from ..utils import require_staff_role


class Collabs(commands.Cog):
    """Coordinate collaboration opportunities for the community."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="collab_open", description="Publish a new collaboration opportunity")
    @require_staff_role()
    async def collab_open(
        self,
        ctx: commands.Context,
        title: str,
        contact: str,
        *,
        description: str,
    ) -> None:
        collab = CollabOpportunity(
            title=title,
            description=description,
            contact=contact,
            status="open",
            created_by=ctx.author.id,
            created_at=datetime.utcnow(),
        )
        collab_id = await self.bot.db.create_collab(collab)

        embed = discord.Embed(title="🤝 Collaboration Opportunity", colour=discord.Colour.green())
        embed.description = description
        embed.add_field(name="Contact", value=contact, inline=False)
        embed.set_footer(text=f"Created by {ctx.author.display_name} • Opportunity #{collab_id}")

        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="collab_list", description="List active collaboration requests")
    async def collab_list(self, ctx: commands.Context, status: Optional[str] = "open") -> None:
        status = status.lower() if status else None
        collabs = await self.bot.db.list_collabs(status=status)

        if not collabs:
            await ctx.reply("No collaboration opportunities found.", mention_author=False)
            return

        embed = discord.Embed(title="🤍 Collaborations", colour=discord.Colour.light_grey())
        for collab in collabs:
            status_text = collab["status"].title()
            value = f"**Status:** {status_text}\n**Contact:** {collab['contact']}\n{collab['description']}"
            embed.add_field(name=f"#{collab['id']} — {collab['title']}", value=value, inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="collab_close", description="Mark a collaboration as filled")
    @require_staff_role()
    async def collab_close(self, ctx: commands.Context, collab_id: int) -> None:
        await self.bot.db.update_collab_status(collab_id, "closed")
        await ctx.reply(f"Collaboration #{collab_id} marked as closed.", mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Collabs(bot))
