"""Support ticket workflow commands."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from ..db import SupportTicket
from ..utils import require_staff_role, require_verified_role


class Support(commands.Cog):
    """Handle community support tickets."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="support", description="Open a support ticket")
    @require_verified_role()
    async def support(self, ctx: commands.Context, *, issue: str) -> None:
        ticket = SupportTicket(
            user_id=ctx.author.id,
            issue=issue,
            status="open",
            created_at=datetime.utcnow(),
        )
        ticket_id = await self.bot.db.create_support_ticket(ticket)
        await ctx.reply(
            f"Support ticket #{ticket_id} opened. We'll reach out shortly, {ctx.author.mention}.",
            mention_author=False,
        )

    @commands.hybrid_command(name="support_list", description="List support tickets")
    @require_staff_role()
    async def support_list(self, ctx: commands.Context, status: Optional[str] = "open") -> None:
        tickets = await self.bot.db.list_support_tickets(status=status.lower() if status else None)
        if not tickets:
            await ctx.reply("No support tickets found for that filter.", mention_author=False)
            return

        embed = discord.Embed(title="💌 Support Tickets", colour=discord.Colour.blue())
        for ticket in tickets[:10]:
            member = ctx.guild.get_member(ticket["user_id"]) if ctx.guild else None
            requester = member.display_name if member else f"User {ticket['user_id']}"
            embed.add_field(
                name=f"#{ticket['id']} — {requester}",
                value=f"**Status:** {ticket['status'].title()}\n{ticket['issue']}",
                inline=False,
            )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="support_close", description="Close a support ticket")
    @require_staff_role()
    async def support_close(self, ctx: commands.Context, ticket_id: int) -> None:
        await self.bot.db.update_support_ticket(ticket_id, "closed")
        await ctx.reply(f"Support ticket #{ticket_id} closed.", mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Support(bot))
