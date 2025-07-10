"""
Command cogs for Victor bot
All Discord commands and interactions
"""

import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random
import string
import logging
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class VerificationCog(commands.Cog):
    """User verification commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify", description="Start the Highrise account verification process")
    async def verify(self, interaction: discord.Interaction, highrise_username: str):
        """Start verification process"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Check if user exists in database
            user_data = await self.bot.db.get_user_by_discord_id(str(interaction.user.id))

            if not user_data:
                # Create new user
                user_id = await self.bot.db.create_user(
                    str(interaction.user.id), 
                    str(interaction.user)
                )
                logger.info(f"Created new user {interaction.user} with ID {user_id}")
            else:
                user_id = user_data['id']
                if user_data['status'] == 'verified':
                    embed = discord.Embed(
                        title="✅ Already Verified",
                        description="Your account is already verified!",
                        color=0x00FF00
                    )
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

            # Check if Highrise username is already taken (case-insensitive)
            existing_user = await self.bot.db.get_user_by_highrise_username_case_insensitive(highrise_username)
            if existing_user and existing_user['id'] != user_id:
                embed = discord.Embed(
                    title="❌ Username Taken",
                    description=f"The Highrise username `{highrise_username}` is already linked to another account.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Verify Highrise username exists (case-insensitive search)
            highrise_user = await self._get_highrise_user(highrise_username)
            if not highrise_user:
                embed = discord.Embed(
                    title="❌ User Not Found",
                    description=f"Could not find Highrise user `{highrise_username}`. Please check the spelling and try again.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Use the exact username from Highrise API response
            exact_username = highrise_user.get('username') or highrise_user.get('user', {}).get('username') or highrise_username

            # Generate verification code
            verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

            # Update user with verification details using exact username
            await self.bot.db.update_user_verification(
                user_id, 
                exact_username, 
                str(highrise_user.get('user_id', '') or highrise_user.get('user', {}).get('user_id', '')),
                verification_code
            )

            # Send verification instructions
            embed = discord.Embed(
                title="🔐 Verification Required",
                description=(
                    f"To verify your account, please add this code to your Highrise bio:\n\n"
                    f"**`{verification_code}`**\n\n"
                    f"Instructions:\n"
                    f"1. Open Highrise and go to your profile\n"
                    f"2. Edit your bio and add the code above anywhere in your bio\n"
                    f"3. Save your bio changes\n"
                    f"4. Use `/check` to complete verification\n\n"
                    f"⏰ This code will expire in 30 minutes."
                ),
                color=0xFF5FA2
            )
            embed.set_footer(text="Victor - Highrise Trading Bot")

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"User {interaction.user} started verification for {highrise_username}")

        except Exception as e:
            logger.error(f"Error in verify command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred during verification. Please try again later.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="check", description="Check your verification status")
    async def check_verification(self, interaction: discord.Interaction):
        """Check verification status"""
        await interaction.response.defer(ephemeral=True)

        try:
            user_data = await self.bot.db.get_user_by_discord_id(str(interaction.user.id))

            if not user_data:
                embed = discord.Embed(
                    title="❌ Not Started",
                    description="Please use `/verify` to start the verification process first.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if user_data['status'] == 'verified':
                embed = discord.Embed(
                    title="✅ Already Verified",
                    description=f"Your account is verified as `{user_data['highrise_username']}`!",
                    color=0x00FF00
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if not user_data['verification_code']:
                embed = discord.Embed(
                    title="❌ No Verification Started",
                    description="Please use `/verify` to start the verification process.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Check bio for verification code with detailed logging
            highrise_user = await self._get_highrise_user(user_data['highrise_username'])
            if not highrise_user:
                embed = discord.Embed(
                    title="❌ User Not Found",
                    description="Could not find your Highrise profile. Please try verification again.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Extract bio from various possible fields
            bio = ""
            possible_bio_fields = ['bio', 'description', 'about', 'profile_description', 'user_bio']

            for field in possible_bio_fields:
                if field in highrise_user and highrise_user[field]:
                    bio = str(highrise_user[field])
                    logger.info(f"Found bio in field '{field}': {bio[:100]}...")
                    break

            # Also check nested user data
            if not bio and 'user' in highrise_user:
                user_obj = highrise_user['user']
                for field in possible_bio_fields:
                    if field in user_obj and user_obj[field]:
                        bio = str(user_obj[field])
                        logger.info(f"Found bio in user.{field}: {bio[:100]}...")
                        break

            verification_code = user_data['verification_code']
            logger.info(f"Looking for verification code '{verification_code}' in bio: '{bio}'")

            # Check for verification code (case-insensitive and flexible)
            code_found = (
                verification_code.upper() in bio.upper() or
                verification_code.lower() in bio.lower() or
                verification_code in bio
            )

            if code_found:
                # Verification successful - update username to match Highrise exactly
                actual_username = highrise_user.get('username') or highrise_user.get('user', {}).get('username')
                if actual_username:
                    await self.bot.db.update_user_highrise_username(user_data['id'], actual_username)

                await self.bot.db.verify_user(user_data['id'])

                embed = discord.Embed(
                    title="🎉 Verification Complete!",
                    description=(
                        f"Congratulations! Your account has been verified.\n\n"
                        f"**Discord:** {interaction.user.mention}\n"
                        f"**Highrise:** `{actual_username or user_data['highrise_username']}`\n\n"
                        f"You can now use all marketplace features!"
                    ),
                    color=0x00FF00
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.info(f"User {interaction.user} verified as {actual_username or user_data['highrise_username']}")

                # Update Discord nickname to match Highrise username
                try:
                    if actual_username and interaction.guild:
                        await interaction.user.edit(nick=actual_username)
                        logger.info(f"Updated Discord nickname to {actual_username}")
                except discord.Forbidden:
                    logger.warning(f"Could not update nickname for {interaction.user} - insufficient permissions")
                except Exception as e:
                    logger.error(f"Error updating nickname: {e}")

            else:
                # Enhanced error message with bio debugging info
                bio_preview = bio[:200] + "..." if len(bio) > 200 else bio
                embed = discord.Embed(
                    title="❌ Code Not Found",
                    description=(
                        f"The verification code `{verification_code}` was not found in your bio.\n\n"
                        f"**Current bio content:** {bio_preview if bio else 'No bio found'}\n\n"
                        f"Please make sure you:\n"
                        f"1. Added the exact code `{verification_code}` to your Highrise bio\n"
                        f"2. Saved your bio changes in the Highrise app\n"
                        f"3. Wait 2-3 minutes for changes to sync\n"
                        f"4. Try again with `/check`"
                    ),
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in check command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while checking verification. Please try again later.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def _get_highrise_user(self, username: str) -> Optional[dict]:
        """Get Highrise user data from API"""
        from bot.utils import HighriseAPI
        return await HighriseAPI.get_user_by_username(username)

class MarketplaceCog(commands.Cog):
    """Marketplace commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sell", description="List an item for sale in the marketplace")
    async def sell_item(self, interaction: discord.Interaction, 
                       item_name: str, category: str, price: int, 
                       description: str = "", contact: str = "Discord DM"):
        """Create a marketplace listing"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Check if user is verified
            user_data = await self.bot.db.get_user_by_discord_id(str(interaction.user.id))

            if not user_data or user_data['status'] != 'verified':
                embed = discord.Embed(
                    title="❌ Verification Required",
                    description="You must be verified to create marketplace listings. Use `/verify` to get started.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if price <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Price",
                    description="Price must be greater than 0 coins.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Create listing
            listing_id = await self.bot.db.create_listing(
                user_data['id'], item_name, category, price, description, contact
            )

            embed = discord.Embed(
                title="✅ Listing Created",
                description=(
                    f"Your item has been listed in the marketplace!\n\n"
                    f"**Item:** {item_name}\n"
                    f"**Category:** {category}\n"
                    f"**Price:** {price:,} coins\n"
                    f"**Contact:** {contact}\n\n"
                    f"Listing ID: `{listing_id}`"
                ),
                color=0x00FF00
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.info(f"User {interaction.user} created listing {listing_id}")

        except Exception as e:
            logger.error(f"Error in sell command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while creating your listing. Please try again later.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="marketplace", description="Browse the marketplace")
    async def browse_marketplace(self, interaction: discord.Interaction, 
                               search: str = "", category: str = ""):
        """Browse marketplace listings"""
        await interaction.response.defer()

        try:
            if search or category:
                listings = await self.bot.db.search_listings(search, category if category else None)
            else:
                listings = await self.bot.db.get_active_listings(limit=10)

            if not listings:
                embed = discord.Embed(
                    title="🛍️ Marketplace",
                    description="No items found matching your criteria.",
                    color=0xFF5FA2
                )
                await interaction.followup.send(embed=embed)
                return

            embed = discord.Embed(
                title="🛍️ Marketplace",
                description=f"Found {len(listings)} item(s)",
                color=0xFF5FA2
            )

            for listing in listings[:5]:  # Show first 5 items
                seller = listing.get('highrise_username', listing.get('discord_username', 'Unknown'))
                embed.add_field(
                    name=f"{listing['item_name']} - {listing['price']:,} coins",
                    value=(
                        f"**Category:** {listing['item_category']}\n"
                        f"**Seller:** {seller}\n"
                        f"**Contact:** {listing['contact_method']}\n"
                        f"**Description:** {listing['description'][:100]}{'...' if len(listing['description']) > 100 else ''}"
                    ),
                    inline=False
                )

            if len(listings) > 5:
                embed.set_footer(text=f"Showing 5 of {len(listings)} items. Use search to narrow results.")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in marketplace command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while browsing the marketplace. Please try again later.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="mylistings", description="View your active listings")
    async def my_listings(self, interaction: discord.Interaction):
        """View user's listings"""
        await interaction.response.defer(ephemeral=True)

        try:
            user_data = await self.bot.db.get_user_by_discord_id(str(interaction.user.id))

            if not user_data:
                embed = discord.Embed(
                    title="❌ Not Registered",
                    description="You need to verify your account first. Use `/verify` to get started.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            listings = await self.bot.db.get_user_listings(user_data['id'])

            if not listings:
                embed = discord.Embed(
                    title="📦 Your Listings",
                    description="You don't have any listings yet. Use `/sell` to create one!",
                    color=0xFF5FA2
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(
                title="📦 Your Listings",
                description=f"You have {len(listings)} listing(s)",
                color=0xFF5FA2
            )

            for listing in listings[:10]:  # Show first 10 listings
                status_emoji = "🟢" if listing['status'] == 'active' else "🔴"
                embed.add_field(
                    name=f"{status_emoji} {listing['item_name']} - {listing['price']:,} coins",
                    value=(
                        f"**Category:** {listing['item_category']}\n"
                        f"**Status:** {listing['status'].title()}\n"
                        f"**Created:** {listing['created_at'][:10]}\n"
                        f"**ID:** {listing['id']}"
                    ),
                    inline=True
                )

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in mylistings command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while fetching your listings. Please try again later.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="sell_gold", description="Sell gold on the marketplace")
    async def sell_gold(self, interaction: discord.Interaction, amount: int, price_per_gold: int):
        """Sell a specified amount of gold"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Check if user is verified
            user_data = await self.bot.db.get_user_by_discord_id(str(interaction.user.id))

            if not user_data or user_data['status'] != 'verified':
                embed = discord.Embed(
                    title="❌ Verification Required",
                    description="You must be verified to create marketplace listings. Use `/verify` to get started.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if amount <= 0 or price_per_gold <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Amount/Price",
                    description="Amount and price per gold must be greater than 0.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            total_price = amount * price_per_gold

            # Create gold listing
            listing_id = await self.bot.db.create_listing(
                user_data['id'], 
                f"{amount:,} Gold", 
                "Gold", 
                total_price,
                f"{amount:,} gold at {price_per_gold} coins per gold",
                "Discord DM"
            )

            embed = discord.Embed(
                title="🪙 Gold Listed Successfully",
                description=(
                    f"Your gold has been listed in the marketplace!\n\n"
                    f"**Amount:** {amount:,} gold\n"
                    f"**Price per gold:** {price_per_gold:,} coins\n"
                    f"**Total price:** {total_price:,} coins\n\n"
                    f"Listing ID: `{listing_id}`"
                ),
                color=0xFFD700
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send notification to marketplace channel if configured
            # This would need a channel ID configured in your bot settings
            logger.info(f"User {interaction.user} listed {amount} gold for {total_price} coins")

        except Exception as e:
            logger.error(f"Error in sell_gold command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while listing your gold. Please try again later.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="sell_nft", description="Sell an NFT on the marketplace")
    async def sell_nft(self, interaction: discord.Interaction, nft_name: str, price: int, description: str = ""):
        """Sell an NFT for a specified price"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Check if user is verified
            user_data = await self.bot.db.get_user_by_discord_id(str(interaction.user.id))

            if not user_data or user_data['status'] != 'verified':
                embed = discord.Embed(
                    title="❌ Verification Required",
                    description="You must be verified to create marketplace listings. Use `/verify` to get started.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            if price <= 0:
                embed = discord.Embed(
                    title="❌ Invalid Price",
                    description="Price must be greater than 0 coins.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Create NFT listing
            listing_id = await self.bot.db.create_listing(
                user_data['id'],
                nft_name,
                "NFT",
                price,
                description if description else f"NFT: {nft_name}",
                "Discord DM"
            )

            embed = discord.Embed(
                title="🎨 NFT Listed Successfully",
                description=(
                    f"Your NFT has been listed in the marketplace!\n\n"
                    f"**NFT Name:** {nft_name}\n"
                    f"**Price:** {price:,} coins\n"
                    f"**Description:** {description if description else 'None provided'}\n\n"
                    f"Listing ID: `{listing_id}`"
                ),
                color=0xFF5FA2
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Send notification to marketplace channel if configured
            logger.info(f"User {interaction.user} listed NFT '{nft_name}' for {price} coins")

        except Exception as e:
            logger.error(f"Error in sell_nft command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while listing your NFT. Please try again later.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

class AdminCog(commands.Cog):
    """Admin commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stats", description="View bot statistics")
    @app_commands.default_permissions(administrator=True)
    async def stats(self, interaction: discord.Interaction):
        """Show bot statistics"""
        await interaction.response.defer()

        try:
            user_stats = await self.bot.db.get_user_stats()

            embed = discord.Embed(
                title="📊 Victor Statistics",
                color=0xFF5FA2
            )

            embed.add_field(
                name="👥 Users",
                value=(
                    f"**Total:** {user_stats['total']}\n"
                    f"**Verified:** {user_stats['verified']}\n"
                    f"**Pending:** {user_stats['pending']}"
                ),
                inline=True
            )

            embed.add_field(
                name="🏢 Guilds",
                value=f"**Connected:** {len(self.bot.guilds)}",
                inline=True
            )

            embed.add_field(
                name="🤖 Bot",
                value=(
                    f"**Uptime:** Online\n"
                    f"**Commands:** {len(self.bot.tree.get_commands())}\n"
                    f"**Latency:** {round(self.bot.latency * 1000)}ms"
                ),
                inline=True
            )

            embed.set_footer(text="Victor - Highrise Trading Bot")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in stats command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while fetching statistics.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed)

class UtilityCog(commands.Cog):
    """Utility commands"""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Get help with Victor's commands")
    async def help_command(self, interaction: discord.Interaction):
        """Show help information"""
        embed = discord.Embed(
            title="🔮 Victor's Commands",
            description="Welcome to the shadows of Highrise trading...",
            color=0xFF5FA2
        )

        embed.add_field(
            name="🔐 Verification",
            value=(
                "`/verify <username>` - Start verification with your Highrise username\n"
                "`/check` - Check your verification status"
            ),
            inline=False
        )

        embed.add_field(
            name="🛍️ Marketplace",
            value=(
                "`/sell <item> <category> <price>` - List an item for sale\n"
                "`/marketplace [search] [category]` - Browse listings\n"
                "`/mylistings` - View your active listings"
            ),
            inline=False
        )

        embed.add_field(
            name="ℹ️ Other",
            value=(
                "`/stats` - View bot statistics (admin only)\n"
                "`/project_overview` - Get project status via DM\n"
                "`/help` - Show this help message"
            ),
            inline=False
        )

        embed.set_footer(text="Victor - Your darkness awaits at the web dashboard")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="project_overview", description="Get a detailed project overview via DM")
    async def project_overview(self, interaction: discord.Interaction):
        """Send project overview via DM"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Create comprehensive project overview
            overview_embed = discord.Embed(
                title="🔮 Victor Bot - Project Overview",
                description="Complete development status and recommendations",
                color=0xFF5FA2
            )

            overview_embed.add_field(
                name="✅ Accomplishments",
                value=(
                    "• **User Verification System** - Two-step verification with Highrise bio validation\n"
                    "• **Marketplace Features** - Item listing, browsing, and purchase facilitation\n"
                    "• **Admin Dashboard** - Flask web interface with real-time analytics\n"
                    "• **Command System** - Organized cogs with slash commands\n"
                    "• **Highrise API Integration** - Profile fetching and verification\n"
                    "• **Database Management** - SQLAlchemy with auto-migration support\n"
                    "• **24/7 Uptime** - Keep-alive system with health monitoring"
                ),
                inline=False
            )

            overview_embed.add_field(
                name="🚀 Recommended Additions",
                value=(
                    "• **Gold Trading** - `/sell_gold <amount>` and `/buy_gold` commands\n"
                    "• **NFT Marketplace** - `/sell_nft <name> <price>` command\n"
                    "• **Notification System** - Channel alerts for transactions\n"
                    "• **Verification Notifications** - New user confirmation messages\n"
                    "• **Enhanced Moderation** - Auto-remove expired listings\n"
                    "• **User Feedback** - Rating system for transactions"
                ),
                inline=False
            )

            overview_embed.add_field(
                name="🎯 Next Steps",
                value=(
                    "1. Add gold and NFT trading commands\n"
                    "2. Implement notification channels\n"
                    "3. Create verification confirmation system\n"
                    "4. Add transaction history tracking\n"
                    "5. Implement user rating system\n"
                    "6. Consider PostgreSQL migration for scale"
                ),
                inline=False
            )

            overview_embed.set_footer(text="Victor - Darkness guides development")

            # Try to send DM
            try:
                await interaction.user.send(embed=overview_embed)

                # Send confirmation
                confirmation_embed = discord.Embed(
                    title="📨 Message Sent",
                    description="Project overview has been sent to your DMs!",
                    color=0x00FF00
                )
                await interaction.followup.send(embed=confirmation_embed, ephemeral=True)

                logger.info(f"Sent project overview DM to {interaction.user}")

            except discord.Forbidden:
                # User has DMs disabled, send here instead
                fallback_embed = discord.Embed(
                    title="⚠️ DM Failed",
                    description="I couldn't send you a DM. Here's the project overview:",
                    color=0xFFAA00
                )
                await interaction.followup.send(embed=fallback_embed, ephemeral=True)
                await interaction.followup.send(embed=overview_embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error in project_overview command: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="An error occurred while generating the project overview.",
                color=0xFF0000
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

async def setup_commands(bot):
    """Setup all command cogs"""
    await bot.add_cog(VerificationCog(bot))
    await bot.add_cog(MarketplaceCog(bot))
    await bot.add_cog(AdminCog(bot))
    await bot.add_cog(UtilityCog(bot))
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging
from datetime import datetime, timedelta
import random
import string
from ..database import get_user_by_discord_id, get_all_listings, get_listing_by_id, create_listing, mark_listing_sold, User, db
from ..utils import fetch_highrise_profile

logger = logging.getLogger(__name__)

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_giveaways = {}

    @app_commands.command(name="verify", description="Verify your Highrise account")
    @app_commands.describe(highrise_username="Your Highrise username")
    @app_commands.cooldown(1, 60.0, key=lambda i: i.user.id)
    async def verify(self, interaction: discord.Interaction, highrise_username: str):
        """Verify Highrise account via bio check"""
        await interaction.response.defer(ephemeral=True)

        try:
            # Generate verification code
            verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

            # Check if user already exists
            existing_user = await get_user_by_discord_id(interaction.user.id)
            if existing_user and existing_user.verified:
                embed = discord.Embed(
                    title="✅ Already Verified",
                    description=f"You are already verified as: **{existing_user.highrise_username}**",
                    color=0x00FF00
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return

            # Store verification attempt
            if existing_user:
                existing_user.verification_code = verification_code
                existing_user.highrise_username = highrise_username
                db.session.commit()
            else:
                user = User(
                    discord_id=interaction.user.id,
                    discord_username=str(interaction.user),
                    highrise_username=highrise_username,
                    verification_code=verification_code
                )
                db.session.add(user)
                db.session.commit()

            # Create verification embed
            embed = discord.Embed(
                title="🔮 Highrise Verification",
                description=(
                    f"To verify your account, add this code to your Highrise bio:\n\n"
                    f"**`{verification_code}`**\n\n"
                    "Once added, click **Check Bio** below."
                ),
                color=0xFF5FA2
            )

            embed.add_field(
                name="📝 Instructions",
                value=(
                    "1. Open Highrise app\n"
                    "2. Go to your profile\n" 
                    "3. Edit your bio\n"
                    "4. Add the code above\n"
                    "5. Click Check Bio button"
                ),
                inline=False
            )

            embed.set_footer(text="Victor - Your darkness awaits")

            # Create view with verification button
            view = VerificationView(verification_code, highrise_username)

            await interaction.followup.send(embed=embed, view=view, ephemeral=