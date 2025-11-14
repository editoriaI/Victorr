"""Feedback collection commands."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from ..db import FeedbackItem
from ..utils import require_staff_role, require_verified_role


class Feedback(commands.Cog):
    """Gather and review community feedback."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="feedback", description="Share feedback with Miss Westie's team")
    @require_verified_role()
    async def feedback(self, ctx: commands.Context, *, message: str) -> None:
        entry = FeedbackItem(
            user_id=ctx.author.id,
            feedback=message,
            status="new",
            created_at=datetime.utcnow(),
        )
        feedback_id = await self.bot.db.store_feedback(entry)
        await ctx.reply(
            f"Thank you for speaking up, {ctx.author.mention}! Feedback #{feedback_id} has been logged.",
            mention_author=False,
        )

    @commands.hybrid_command(name="feedback_list", description="Review submitted feedback")
    @require_staff_role()
    async def feedback_list(self, ctx: commands.Context, status: Optional[str] = None) -> None:
        items = await self.bot.db.list_feedback(status=status.lower() if status else None)
        if not items:
            await ctx.reply("No feedback entries found for that filter.", mention_author=False)
            return

        embed = discord.Embed(title="📝 Feedback Inbox", colour=discord.Colour.teal())
        for item in items[:10]:
            member = ctx.guild.get_member(item["user_id"]) if ctx.guild else None
            author = member.display_name if member else f"User {item['user_id']}"
            embed.add_field(
                name=f"#{item['id']} — {author}",
                value=f"**Status:** {item['status'].title()}\n{item['feedback']}",
                inline=False,
            )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="feedback_status", description="Update a feedback entry")
    @require_staff_role()
    async def feedback_status(self, ctx: commands.Context, feedback_id: int, status: str) -> None:
        await self.bot.db.update_feedback_status(feedback_id, status.lower())
        await ctx.reply(f"Feedback #{feedback_id} updated to {status.title()}.", mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Feedback(bot))
