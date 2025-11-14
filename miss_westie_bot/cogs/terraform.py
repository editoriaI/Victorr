"""Server setup helper commands."""

from __future__ import annotations

import discord
from discord.ext import commands

from ..utils import require_staff_role


class Terraform(commands.Cog):
    """Provide quick utilities for server setup and housekeeping."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="terraform_plan", description="Show the server setup checklist")
    @require_staff_role()
    async def terraform_plan(self, ctx: commands.Context) -> None:
        embed = discord.Embed(title="🏗️ Miss Westie Server Terraform Plan", colour=discord.Colour.brand_green())
        embed.add_field(
            name="Essentials",
            value=(
                "• Configure verification flow\n"
                "• Enable onboarding prompts\n"
                "• Ensure safety automations are online"
            ),
            inline=False,
        )
        embed.add_field(
            name="Channels",
            value=(
                "• Music drops + announcements\n"
                "• Producer lounge\n"
                "• Collab board\n"
                "• Feedback + support"
            ),
            inline=False,
        )
        embed.add_field(
            name="Roles",
            value=(
                "• Verified listeners\n"
                "• Producers\n"
                "• Collab partners\n"
                "• Support squad"
            ),
            inline=False,
        )
        embed.set_footer(text="Use /terraform_sync to refresh bot cogs after making changes.")
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(name="terraform_sync", description="Reload bot cogs after making changes")
    @require_staff_role()
    async def terraform_sync(self, ctx: commands.Context) -> None:
        reloaded: list[str] = []
        for extension in list(self.bot.extensions.keys()):
            if not extension.startswith("miss_westie_bot.cogs"):
                continue
            await self.bot.reload_extension(extension)
            reloaded.append(extension.split(".")[-1])

        message = "Reloaded cogs: " + ", ".join(sorted(reloaded)) if reloaded else "No cogs were reloaded."
        await ctx.reply(message, mention_author=False)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Terraform(bot))
