"""Producer spotlight utilities."""

from __future__ import annotations

from datetime import datetime

import discord
from discord.ext import commands

from ..db import RoleRequest
from ..utils import require_staff_role, require_verified_role


class Producers(commands.Cog):
    """Manage producer highlights and requests."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="producer_request", description="Request to be added to the producer roster")
    @require_verified_role()
    async def producer_request(self, ctx: commands.Context) -> None:
        request = RoleRequest(
            user_id=ctx.author.id,
            role_name="Producer",
            status="pending",
            created_at=datetime.utcnow(),
        )
        request_id = await self.bot.db.create_role_request(request)
        await ctx.reply(
            f"Thanks for your submission, {ctx.author.mention}! Request #{request_id} has been recorded.",
            mention_author=False,
        )

    @commands.hybrid_command(name="producer_approve", description="Approve a producer request")
    @require_staff_role()
    async def producer_approve(self, ctx: commands.Context, request_id: int) -> None:
        await self.bot.db.update_role_request(request_id, "approved")
        await ctx.reply(f"Producer request #{request_id} approved.", mention_author=False)

    @commands.hybrid_command(name="producers", description="List approved producers")
    async def producers(self, ctx: commands.Context) -> None:
        requests = await self.bot.db.list_role_requests()
        approved = [req for req in requests if req["role_name"].lower() == "producer" and req["status"] == "approved"]

        if not approved:
            await ctx.reply("No approved producers yet — encourage your favourites to apply!", mention_author=False)
            return

        embed = discord.Embed(title="🎚️ Featured Producers", colour=discord.Colour.gold())
        for entry in approved:
            member = ctx.guild.get_member(entry["user_id"]) if ctx.guild else None
            display_name = member.display_name if member else f"<@{entry['user_id']}>"
            embed.add_field(name=display_name, value=f"Added on {entry['created_at'][:10]}", inline=False)

        await ctx.reply(embed=embed, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Producers(bot))
