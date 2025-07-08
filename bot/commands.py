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
            
            # Check if Highrise username is already taken
            existing_user = await self.bot.db.get_user_by_highrise_username(highrise_username)
            if existing_user and existing_user['id'] != user_id:
                embed = discord.Embed(
                    title="❌ Username Taken",
                    description=f"The Highrise username `{highrise_username}` is already linked to another account.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Verify Highrise username exists
            highrise_user = await self._get_highrise_user(highrise_username)
            if not highrise_user:
                embed = discord.Embed(
                    title="❌ User Not Found",
                    description=f"Could not find Highrise user `{highrise_username}`. Please check the spelling.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Generate verification code
            verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            # Update user with verification details
            await self.bot.db.update_user_verification(
                user_id, 
                highrise_username, 
                str(highrise_user.get('user_id', '')),
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
            
            # Check bio for verification code
            highrise_user = await self._get_highrise_user(user_data['highrise_username'])
            if not highrise_user:
                embed = discord.Embed(
                    title="❌ User Not Found",
                    description="Could not find your Highrise profile. Please try verification again.",
                    color=0xFF0000
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            bio = highrise_user.get('bio', '')
            verification_code = user_data['verification_code']
            
            if verification_code in bio:
                # Verification successful
                await self.bot.db.verify_user(user_data['id'])
                
                embed = discord.Embed(
                    title="🎉 Verification Complete!",
                    description=(
                        f"Congratulations! Your account has been verified.\n\n"
                        f"**Discord:** {interaction.user.mention}\n"
                        f"**Highrise:** `{user_data['highrise_username']}`\n\n"
                        f"You can now use all marketplace features!"
                    ),
                    color=0x00FF00
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.info(f"User {interaction.user} verified as {user_data['highrise_username']}")
            else:
                embed = discord.Embed(
                    title="❌ Code Not Found",
                    description=(
                        f"The verification code `{verification_code}` was not found in your bio.\n\n"
                        f"Please make sure you:\n"
                        f"1. Added the code to your Highrise bio\n"
                        f"2. Saved your bio changes\n"
                        f"3. Wait a few minutes for the changes to update"
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
        try:
            url = f"https://webapi.highrise.game/users?username={username}"
            headers = {
                'User-Agent': 'Victor-Discord-Bot/1.0',
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'users' in data and data['users']:
                            return data['users'][0]
            return None
        except Exception as e:
            logger.error(f"Error getting Highrise user {username}: {e}")
            return None

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
                "`/help` - Show this help message"
            ),
            inline=False
        )
        
        embed.set_footer(text="Victor - Your darkness awaits at the web dashboard")
        await interaction.response.send_message(embed=embed)

async def setup_commands(bot):
    """Setup all command cogs"""
    await bot.add_cog(VerificationCog(bot))
    await bot.add_cog(MarketplaceCog(bot))
    await bot.add_cog(AdminCog(bot))
    await bot.add_cog(UtilityCog(bot))
