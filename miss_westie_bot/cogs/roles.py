"""Role request management commands."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands

from ..db import RoleRequest
from ..utils import require_staff_role, require_verified_role


class Roles(commands.Cog):
    """Allow community members to request special roles."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="role_request", description="Request a special community role")
    @require_verified_role()
    async def role_request(self, ctx: commands.Context, *, role_name: str) -> None:
        request = RoleRequest(
            user_id=ctx.author.id,
            role_name=role_name,
            status="pending",
            created_at=datetime.utcnow(),
        )
        request_id = await self.bot.db.create_role_request(request)
        await ctx.reply(
            f"Role request #{request_id} submitted for '{role_name}'. We'll be in touch soon!",
            mention_author=False,
        )

    @commands.hybrid_command(name="role_requests", description="View pending role requests")
    @require_staff_role()
    async def role_requests(self, ctx: commands.Context, status: Optional[str] = "pending") -> None:
        entries = await self.bot.db.list_role_requests(status=status.lower() if status else None)
        if not entries:
            await ctx.reply("No role requests found for that filter.", mention_author=False)
            return

        embed = discord.Embed(title="🎀 Role Requests", colour=discord.Colour.brand_red())
        for entry in entries[:10]:
            member = ctx.guild.get_member(entry["user_id"]) if ctx.guild else None
            requester = member.display_name if member else f"User {entry['user_id']}"
            embed.add_field(
                name=f"#{entry['id']} — {requester}",
                value=f"**Role:** {entry['role_name']}\n**Status:** {entry['status'].title()}",
                inline=False,
            )
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="role_status", description="Update a role request status")
    @require_staff_role()
    async def role_status(self, ctx: commands.Context, request_id: int, status: str) -> None:
        await self.bot.db.update_role_request(request_id, status.lower())
        await ctx.reply(f"Role request #{request_id} updated to {status.title()}.", mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Roles(bot))
