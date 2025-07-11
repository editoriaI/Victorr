import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import random
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

class SellView(discord.ui.View):
    def __init__(self, seller_id, item_name, price):
        super().__init__(timeout=None)
        self.seller_id = seller_id
        self.item_name = item_name
        self.price = price

    @discord.ui.button(label='📩 Notify Seller', style=discord.ButtonStyle.secondary, emoji='📩', custom_id='notify_seller_button')
    async def notify_seller(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            seller = interaction.guild.get_member(self.seller_id)
            if seller:
                # DM the seller
                embed = discord.Embed(
                    title="🔔 Interest in Your Listing",
                    description=f"Someone is interested in your listing for: **{self.item_name}** (**{self.price}**). Please respond in the listing channel if still available.",
                    color=0x8B0000,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text="Victor's Marketplace Notifications", icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png")

                try:
                    await seller.send(embed=embed)
                    await interaction.response.send_message("✅ Seller has been notified!", ephemeral=True)
                except:
                    await interaction.response.send_message("❌ Could not notify seller (DMs may be disabled)", ephemeral=True)

                # Log to interest-pings if it exists
                interest_channel = discord.utils.get(interaction.guild.channels, name="interest-pings")
                if interest_channel:
                    log_embed = discord.Embed(
                        title="📩 Listing Interest",
                        description=f"{interaction.user.mention} showed interest in {seller.mention}'s listing: **{self.item_name}**",
                        color=0x8B0000,
                        timestamp=datetime.utcnow()
                    )
                    await interest_channel.send(embed=log_embed)
            else:
                await interaction.response.send_message("❌ Seller not found", ephemeral=True)
        except Exception as e:
            logger.error(f"Error in notify_seller: {e}")
            await interaction.response.send_message("❌ An error occurred", ephemeral=True)

class MarketplaceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def has_required_roles(self, member):
        """Check if user has both Rules Accepted and Verified roles"""
        rules_accepted = discord.utils.get(member.roles, name="Rules Accepted")
        verified = discord.utils.get(member.roles, name="Verified")
        return rules_accepted and verified

    @app_commands.command(name="sell", description="Sell an item, gold, or NFT")
    @app_commands.describe(
        type="What type of item to sell",
        name="Name of the item/NFT or amount of gold",
        price="Price in coins",
        description="Optional description"
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Item", value="item"),
        app_commands.Choice(name="Gold", value="gold"),
        app_commands.Choice(name="NFT", value="nft")
    ])
    async def sell(self, interaction: discord.Interaction, type: str, name: str, price: int, description: str = ""):
        if not self.has_required_roles(interaction.user):
            embed = discord.Embed(
                title="🚫 Access Denied",
                description="You need both **@Rules Accepted** and **@Verified** roles to use marketplace commands.",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        await interaction.response.defer()

        try:
            # Determine target channel
            channel_map = {
                "item": "item-sales",
                "gold": "gold-sales", 
                "nft": "nft-sales"
            }

            target_channel = discord.utils.get(interaction.guild.channels, name=channel_map[type])
            if not target_channel:
                await interaction.followup.send(f"❌ Channel #{channel_map[type]} not found", ephemeral=True)
                return

            # Create embed with Victor's styling
            embed = discord.Embed(
                title=f"💀 {type.upper()} FOR SALE",
                color=0x8B0000,
                timestamp=datetime.utcnow()
            )

            if type == "gold":
                embed.add_field(name="💰 Amount", value=f"{name:,}", inline=True)
                embed.add_field(name="💎 Total Price", value=f"{price:,} coins", inline=True)
                embed.add_field(name="📊 Rate", value=f"{price/int(name)*1000:.1f} per 1k", inline=True)
            else:
                embed.add_field(name="📦 Item" if type == "item" else "🎨 NFT", value=name, inline=True)
                embed.add_field(name="💎 Price", value=f"{price:,} coins", inline=True)

            if description:
                embed.add_field(name="📝 Description", value=description, inline=False)

            embed.add_field(name="👤 Seller", value=interaction.user.mention, inline=True)
            embed.set_footer(text="Victor's Marketplace", icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png")

            # Create view with notify button
            view = SellView(interaction.user.id, name, f"{price:,} coins")

            await target_channel.send(embed=embed, view=view)
            await interaction.followup.send(f"✅ Your {type} has been listed in {target_channel.mention}!", ephemeral=True)

        except Exception as e:
            logger.error(f"Error in sell command: {e}")
            await interaction.followup.send("❌ An error occurred while creating your listing", ephemeral=True)

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify", description="Verify your Highrise account")
    @app_commands.describe(username="Your Highrise username")
    async def verify(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer(ephemeral=True)

        try:
            # Add user to database as verified
            user_data = {
                'discord_id': str(interaction.user.id),
                'discord_username': str(interaction.user),
                'highrise_username': username,
                'status': 'verified',
                'verified_at': datetime.utcnow()
            }

            await self.bot.db.create_or_update_user(user_data)

            # Assign Verified role
            verified_role = discord.utils.get(interaction.guild.roles, name="Verified")
            if verified_role:
                await interaction.user.add_roles(verified_role)

            # Update nickname to Highrise username
            try:
                await interaction.user.edit(nick=username)
            except:
                pass  # May fail due to permissions

            # Send embed to new-user-verification channel
            verification_channel = discord.utils.get(interaction.guild.channels, name="new-user-verification")
            if verification_channel:
                embed = discord.Embed(
                    title="✅ User Verified",
                    color=0x00FF00,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="Discord User", value=interaction.user.mention, inline=True)
                embed.add_field(name="Highrise", value=f"@{username}", inline=True)
                embed.set_footer(text="Victor's Verification System")

                await verification_channel.send(embed=embed)

            # DM welcome message
            welcome_embed = discord.Embed(
                title="🎉 Welcome to the Highrise Blacklist!",
                description=f"Greetings, {username}. Victor welcomes you to the shadows of the marketplace.",
                color=0x8B0000
            )
            welcome_embed.add_field(
                name="📜 Server Guide",
                value="• React ✅ in #rules to gain access\n• Use `/sell` commands in marketplace\n• Follow all server rules\n• Enjoy your stay in the darkness...",
                inline=False
            )
            welcome_embed.set_footer(text="Victor's Undead Concierge Service")

            try:
                await interaction.user.send(embed=welcome_embed)
            except:
                pass  # User may have DMs disabled

            await interaction.followup.send(f"✅ Verification complete! Welcome, {username}.", ephemeral=True)

        except Exception as e:
            logger.error(f"Error in verify command: {e}")
            await interaction.followup.send("❌ Verification failed. Please try again.", ephemeral=True)

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="purge_listings", description="Clear old marketplace listings")
    @app_commands.checks.has_role("owner of this house")
    @app_commands.describe(days="Remove listings older than X days (default: 30)")
    async def purge_listings(self, interaction: discord.Interaction, days: int = 30):
        await interaction.response.defer()

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get marketplace channels
            marketplace_channels = ["item-sales", "gold-sales", "nft-sales"]
            total_deleted = 0
            
            for channel_name in marketplace_channels:
                channel = discord.utils.get(interaction.guild.channels, name=channel_name)
                if not channel:
                    continue
                    
                deleted_count = 0
                async for message in channel.history(limit=None):
                    if message.created_at < cutoff_date and message.author.id == self.bot.user.id:
                        try:
                            await message.delete()
                            deleted_count += 1
                            await asyncio.sleep(0.5)  # Rate limit protection
                        except:
                            continue
                
                total_deleted += deleted_count
                logger.info(f"Deleted {deleted_count} old listings from #{channel_name}")

            embed = discord.Embed(
                title="🧹 Marketplace Cleanup Complete",
                description=f"Removed **{total_deleted}** listings older than {days} days from the marketplace channels.",
                color=0x8B0000,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Victor's Marketplace Management")
            
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in purge_listings: {e}")
            await interaction.followup.send("❌ Failed to purge listings", ephemeral=True)

    @app_commands.command(name="giveaway", description="Start a giveaway")
    @app_commands.checks.has_role("owner of this house")
    @app_commands.describe(
        prize="What is being given away",
        duration="Duration (e.g., 10m, 1h, 2d)"
    )
    async def giveaway(self, interaction: discord.Interaction, prize: str, duration: str):
        await interaction.response.defer()

        try:
            # Parse duration
            time_regex = re.match(r'(\d+)([mhd])', duration.lower())
            if not time_regex:
                await interaction.followup.send("❌ Invalid duration format. Use format like '10m', '1h', '2d'", ephemeral=True)
                return

            amount, unit = time_regex.groups()
            amount = int(amount)

            if unit == 'm':
                end_time = datetime.utcnow() + timedelta(minutes=amount)
            elif unit == 'h':
                end_time = datetime.utcnow() + timedelta(hours=amount)
            elif unit == 'd':
                end_time = datetime.utcnow() + timedelta(days=amount)

            # Find giveaway channel
            giveaway_channel = discord.utils.get(interaction.guild.channels, name="giveaway")
            if not giveaway_channel:
                await interaction.followup.send("❌ #giveaway channel not found", ephemeral=True)
                return

            # Create giveaway embed
            embed = discord.Embed(
                title="🎉 GIVEAWAY",
                description=f"**Prize:** {prize}\n\n**How to Enter:**\nReact with 🎉 to enter!\n\n**Ends:** <t:{int(end_time.timestamp())}:R>",
                color=0x8B0000,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text="Victor's Giveaway System")

            giveaway_msg = await giveaway_channel.send(embed=embed)
            await giveaway_msg.add_reaction("🎉")

            await interaction.followup.send(f"✅ Giveaway started in {giveaway_channel.mention}!")

            # Wait for giveaway to end
            await asyncio.sleep((end_time - datetime.utcnow()).total_seconds())

            # Pick winner
            giveaway_msg = await giveaway_channel.fetch_message(giveaway_msg.id)
            reaction = discord.utils.get(giveaway_msg.reactions, emoji="🎉")

            if reaction and reaction.count > 1:
                users = [user async for user in reaction.users() if not user.bot]
                if users:
                    winner = random.choice(users)

                    winner_embed = discord.Embed(
                        title="🎉 GIVEAWAY ENDED",
                        description=f"**Winner:** {winner.mention}\n**Prize:** {prize}\n\nCongratulations! 🎉",
                        color=0x00FF00,
                        timestamp=datetime.utcnow()
                    )
                    await giveaway_channel.send(embed=winner_embed)
                else:
                    await giveaway_channel.send("😔 No valid entries for the giveaway.")
            else:
                await giveaway_channel.send("😔 No entries for the giveaway.")

        except Exception as e:
            logger.error(f"Error in giveaway command: {e}")
            await interaction.followup.send("❌ An error occurred while starting the giveaway", ephemeral=True)

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="marketplace_stats", description="View marketplace statistics")
    @app_commands.checks.has_role("owner of this house")
    async def marketplace_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            # Get marketplace channels
            marketplace_channels = ["item-sales", "gold-sales", "nft-sales"]
            stats = {}
            total_listings = 0
            
            for channel_name in marketplace_channels:
                channel = discord.utils.get(interaction.guild.channels, name=channel_name)
                if not channel:
                    stats[channel_name] = 0
                    continue
                    
                count = 0
                async for message in channel.history(limit=None):
                    if message.author.id == self.bot.user.id and message.embeds:
                        count += 1
                        
                stats[channel_name] = count
                total_listings += count

            # Get user counts
            verified_users = len([m for m in interaction.guild.members if discord.utils.get(m.roles, name="Verified")])
            trusted_sellers = len([m for m in interaction.guild.members if discord.utils.get(m.roles, name="Trusted Seller")])

            embed = discord.Embed(
                title="📊 Marketplace Statistics",
                description="Current marketplace activity and user metrics",
                color=0x8B0000,
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="🛍️ Active Listings",
                value=f"Items: **{stats.get('item-sales', 0)}**\nGold: **{stats.get('gold-sales', 0)}**\nNFTs: **{stats.get('nft-sales', 0)}**\n**Total: {total_listings}**",
                inline=True
            )
            
            embed.add_field(
                name="👥 User Statistics",
                value=f"Total Members: **{interaction.guild.member_count}**\nVerified: **{verified_users}**\nTrusted Sellers: **{trusted_sellers}**",
                inline=True
            )
            
            embed.set_footer(text="Victor's Analytics System")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Error in marketplace_stats: {e}")
            await interaction.followup.send("❌ Failed to fetch marketplace statistics", ephemeral=True)

    @app_commands.command(name="manage_roles", description="Assign or remove marketplace roles")
    @app_commands.checks.has_role("owner of this house")
    @app_commands.describe(
        user="User to manage",
        action="Add or remove role",
        role="Role to manage"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Add", value="add"),
            app_commands.Choice(name="Remove", value="remove")
        ],
        role=[
            app_commands.Choice(name="Verified", value="Verified"),
            app_commands.Choice(name="Trusted Seller", value="Trusted Seller"),
            app_commands.Choice(name="Rules Accepted", value="Rules Accepted")
        ]
    )
    async def manage_roles(self, interaction: discord.Interaction, user: discord.Member, action: str, role: str):
        await interaction.response.defer(ephemeral=True)

        try:
            target_role = discord.utils.get(interaction.guild.roles, name=role)
            if not target_role:
                await interaction.followup.send(f"❌ Role '{role}' not found", ephemeral=True)
                return

            if action == "add":
                if target_role in user.roles:
                    await interaction.followup.send(f"❌ {user.mention} already has the {role} role", ephemeral=True)
                    return
                    
                await user.add_roles(target_role)
                
                embed = discord.Embed(
                    title="✅ Role Added",
                    description=f"Successfully added **{role}** role to {user.mention}",
                    color=0x00FF00,
                    timestamp=datetime.utcnow()
                )
                
            else:  # remove
                if target_role not in user.roles:
                    await interaction.followup.send(f"❌ {user.mention} doesn't have the {role} role", ephemeral=True)
                    return
                    
                await user.remove_roles(target_role)
                
                embed = discord.Embed(
                    title="🗑️ Role Removed",
                    description=f"Successfully removed **{role}** role from {user.mention}",
                    color=0xFF0000,
                    timestamp=datetime.utcnow()
                )

            embed.set_footer(text="Victor's Role Management System")
            await interaction.followup.send(embed=embed, ephemeral=True)

            # Log to mod-alerts if available
            mod_channel = discord.utils.get(interaction.guild.channels, name="mod-alerts")
            if mod_channel:
                log_embed = discord.Embed(
                    title="👑 Role Management",
                    description=f"{interaction.user.mention} {action}ed **{role}** role {'to' if action == 'add' else 'from'} {user.mention}",
                    color=0x8B0000,
                    timestamp=datetime.utcnow()
                )
                await mod_channel.send(embed=log_embed)

        except Exception as e:
            logger.error(f"Error in manage_roles: {e}")
            await interaction.followup.send("❌ Failed to manage role", ephemeral=True)

    @app_commands.command(name="help", description="View all available commands and features")
    async def help(self, interaction: discord.Interaction):
        # Check user roles
        has_rules_accepted = discord.utils.get(interaction.user.roles, name="Rules Accepted")
        is_verified = discord.utils.get(interaction.user.roles, name="Verified")
        is_admin = discord.utils.get(interaction.user.roles, name="owner of this house")

        embed = discord.Embed(
            title="🧙‍♂️ Victor's Command Guide",
            description="*\"Allow me to guide you through my domain...\"*",
            color=0x8B0000,
            timestamp=datetime.utcnow()
        )

        if not has_rules_accepted:
            embed.add_field(
                name="📜 First Steps",
                value="React with ✅ in the rules channel to gain access to the server and unlock commands.",
                inline=False
            )
        else:
            if not is_verified:
                embed.add_field(
                    name="✅ Verification",
                    value="`/verify <username>` - Link your Highrise account to unlock marketplace access",
                    inline=False
                )
            else:
                embed.add_field(
                    name="🛒 Marketplace Commands",
                    value="`/sell <type> <name> <price>` - List items, gold, or NFTs for sale\n*Requires both Rules Accepted and Verified roles*",
                    inline=False
                )

            embed.add_field(
                name="🎉 Community Commands",
                value="`/giveaway <prize> <duration>` - Start a community giveaway",
                inline=False
            )

        if is_admin:
            embed.add_field(
                name="🔧 Admin Commands",
                value="`/purge_listings <days>` - Remove old marketplace listings\n`/marketplace_stats` - View marketplace analytics\n`/manage_roles <user> <action> <role>` - Assign/remove roles",
                inline=False
            )

        embed.add_field(
            name="📊 Your Status",
            value=f"Rules Accepted: {'✅' if has_rules_accepted else '❌'}\nVerified: {'✅' if is_verified else '❌'}\nAdmin: {'✅' if is_admin else '❌'}",
            inline=True
        )

        embed.set_footer(text="Victor's Guidance System")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class ReactionRoleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id == self.bot.user.id:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel or channel.name != "rules":
            return

        if str(payload.emoji) == "✅":
            member = guild.get_member(payload.user_id)
            if member:
                rules_accepted_role = discord.utils.get(guild.roles, name="Rules Accepted")
                if rules_accepted_role and rules_accepted_role not in member.roles:
                    try:
                        await member.add_roles(rules_accepted_role)
                        logger.info(f"Assigned Rules Accepted role to {member}")
                    except Exception as e:
                        logger.error(f"Error assigning Rules Accepted role: {e}")

async def setup_commands(bot):
    """Setup all command cogs"""
    await bot.add_cog(MarketplaceCog(bot))
    await bot.add_cog(VerificationCog(bot))
    await bot.add_cog(AdminCog(bot))
    await bot.add_cog(UtilityCog(bot))
    await bot.add_cog(ReactionRoleCog(bot))