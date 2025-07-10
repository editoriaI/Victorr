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

    @app_commands.command(name="setup_server", description="Strips and rebuilds the server layout")
    @app_commands.checks.has_role("owner of this house")
    async def setup_server(self, interaction: discord.Interaction):
        await interaction.response.send_message("🛠️ Victor is terraforming the server. Please wait...", ephemeral=True)
        guild = interaction.guild
        
        logger.info(f"🏗️ Starting server terraform for {guild.name}")

        protected_roles = [
            "@everyone", "owner of this house", "event notifications", "giveaway notifications",
            "rare sales values", "services", "room builder", "raffle notifications", "commissions"
        ]

        # Delete channels
        logger.info("🗑️ Clearing existing channels...")
        deleted_channels = 0
        for channel in guild.channels:
            try:
                await channel.delete()
                deleted_channels += 1
            except Exception:
                continue
        logger.info(f"✅ Deleted {deleted_channels} channels")

        # Delete non-protected roles
        logger.info("🗑️ Removing non-essential roles...")
        deleted_roles = 0
        for role in guild.roles:
            name = role.name.lower()
            if role.managed or name in [r.lower() for r in protected_roles] or "ping" in name:
                continue
            try:
                await role.delete()
                deleted_roles += 1
            except Exception:
                continue
        logger.info(f"✅ Deleted {deleted_roles} roles")

        # Create required roles
        logger.info("👑 Creating essential roles...")
        role_names = ["Unverified", "Verified", "Trusted Seller", "Moderator", "Rules Accepted"]
        created_roles = 0
        for name in role_names:
            if not discord.utils.get(guild.roles, name=name):
                await guild.create_role(name=name)
                created_roles += 1
                logger.info(f"  ➕ Created role: {name}")
        logger.info(f"✅ Created {created_roles} new roles")

        # Create channel layout
        logger.info("🏗️ Building Victor's domain...")
        layout = {
            "Welcome": ["rules", "announcements", "new-user-verification"],
            "Marketplace": ["item-sales", "gold-sales", "nft-sales", "sold-alerts"],
            "Listings & Requests": ["wishlist-requests", "interest-pings"],
            "Community": ["art-showcase", "pets", "selfies", "memes", "venting-zone"],
            "Moderation": ["mod-alerts", "flagged-listings", "logs"],
            "Giveaways": ["giveaway"],
            "Pricing": ["price-checks"],
            "Admin": ["victors-vault"]
        }

        total_channels = sum(len(ch_list) for ch_list in layout.values())
        created_channels = 0
        
        for cat_name, ch_list in layout.items():
            logger.info(f"📁 Creating category: {cat_name}")
            category = await guild.create_category(cat_name)
            for ch_name in ch_list:
                channel = await guild.create_text_channel(ch_name, category=category)
                created_channels += 1
                logger.info(f"  ➕ Created #{ch_name} ({created_channels}/{total_channels})")

                # Set permissions for Victor's Vault
                if ch_name == "victors-vault":
                    logger.info("🏛️ Setting up Victor's exclusive vault...")
                    
                    # Deny access to everyone by default
                    await channel.set_permissions(guild.default_role, read_messages=False, send_messages=False)
                    
                    # Grant access to privileged roles
                    owner_role = discord.utils.get(guild.roles, name="owner of this house")
                    mod_role = discord.utils.get(guild.roles, name="Moderator")
                    trusted_role = discord.utils.get(guild.roles, name="Trusted Seller")

                    vault_members = []
                    if owner_role:
                        await channel.set_permissions(owner_role, 
                                                    read_messages=True, 
                                                    send_messages=True, 
                                                    manage_messages=True,
                                                    embed_links=True,
                                                    attach_files=True)
                        vault_members.append("House Owner")
                        
                    if mod_role:
                        await channel.set_permissions(mod_role, 
                                                    read_messages=True, 
                                                    send_messages=True,
                                                    embed_links=True,
                                                    attach_files=True)
                        vault_members.append("Moderators")
                        
                    if trusted_role:
                        await channel.set_permissions(trusted_role, 
                                                    read_messages=True, 
                                                    send_messages=True,
                                                    embed_links=True)
                        vault_members.append("Trusted Sellers")
                    
                    logger.info(f"🔐 Victor's Vault secured! Access granted to: {', '.join(vault_members)}")
                    
                    # Send a welcome message to the vault
                    vault_embed = discord.Embed(
                        title="🏛️ Welcome to Victor's Vault",
                        description="*\"Welcome to my inner sanctum. Here, only the worthy may tread.\"*\n\n"
                                  "This channel is reserved for:\n"
                                  "• 🏠 Server administration\n"
                                  "• 🔒 Private discussions\n"
                                  "• 📊 Analytics and reports\n"
                                  "• 🛠️ Bot configuration\n\n"
                                  "*Remember: What happens in the vault, stays in the vault.*",
                        color=0x8B0000,
                        timestamp=datetime.utcnow()
                    )
                    vault_embed.set_footer(text="Victor's Private Domain")
                    await channel.send(embed=vault_embed)

        logger.info(f"🎉 Server terraform complete! Created {len(layout)} categories and {total_channels} channels")
        
        # Send completion summary
        summary_embed = discord.Embed(
            title="🏗️ Server Terraform Complete",
            description=f"Victor has successfully reconstructed {guild.name}:\n\n"
                       f"📁 **{len(layout)}** categories created\n"
                       f"📝 **{total_channels}** channels created\n"
                       f"👑 **{created_roles}** roles created\n"
                       f"🗑️ **{deleted_channels}** old channels removed\n"
                       f"🗑️ **{deleted_roles}** old roles removed\n\n"
                       f"*\"Another domain falls under my influence...\"*",
            color=0x8B0000,
            timestamp=datetime.utcnow()
        )
        summary_embed.set_footer(text="Victor's Server Terraform System")
        
        await interaction.followup.send(embed=summary_embed)

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

    @app_commands.command(name="victorhq", description="Access Victor's web dashboard")
    async def victorhq(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🌐 Victor HQ Dashboard",
            description="Access Victor's web dashboard for advanced features and management.",
            color=0x8B0000,
            timestamp=datetime.utcnow()
        )
        embed.add_field(
            name="🔗 Dashboard Link",
            value="[**Click here to access Victor HQ**](https://tinyurl.com/VictorHQ)",
            inline=False
        )
        embed.add_field(
            name="📊 Features",
            value="• User management and verification\n• Marketplace analytics\n• Server configuration\n• Activity monitoring\n• Administrative tools",
            inline=False
        )
        embed.set_footer(text="Victor's Web Dashboard", icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="project_overview", description="Get an overview of Victor's capabilities")
    @app_commands.checks.has_role("owner of this house")
    async def project_overview(self, interaction: discord.Interaction):
        overview_text = """Victor is the undead concierge of the Highrise Blacklist. He helps users verify, list items, notify sellers, and manage the black market.

Features:
- Sell gold, NFTs, and items
- Notify sellers of interest
- Verify users before full access
- Reaction-based rules gating
- Server terraform via /setup_server
- Giveaways, price checks, and more"""

        await interaction.response.send_message(overview_text)

    @app_commands.command(name="send_rules", description="Send rules message to the rules channel")
    @app_commands.checks.has_role("owner of this house")
    async def send_rules(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            # Get the rules channel
            rules_channel = interaction.guild.get_channel(1385445808354365580)
            if not rules_channel:
                await interaction.followup.send("❌ Rules channel not found", ephemeral=True)
                return

            # Create comprehensive rules embed
            rules_embed = discord.Embed(
                title="📜 Highrise Blacklist Server Rules",
                description="Welcome to the shadows. Follow these rules to survive in Victor's domain.",
                color=0x8B0000,
                timestamp=datetime.utcnow()
            )

            rules_embed.add_field(
                name="🚫 Rule 1: No Scamming",
                value="Any form of scamming, fraud, or deceptive trading will result in immediate ban. Victor has no patience for thieves.",
                inline=False
            )

            rules_embed.add_field(
                name="🤝 Rule 2: Respect All Members",
                value="Treat everyone with respect. No harassment, bullying, or discrimination. Victor demands civility in his domain.",
                inline=False
            )

            rules_embed.add_field(
                name="📢 Rule 3: Use Correct Channels",
                value="Post content in appropriate channels. Use marketplace channels for trading, general for chat. Organization pleases Victor.",
                inline=False
            )

            rules_embed.add_field(
                name="🔞 Rule 4: Keep Content Appropriate",
                value="No NSFW content, excessive profanity, or inappropriate material. Victor runs a respectable establishment.",
                inline=False
            )

            rules_embed.add_field(
                name="🚨 Rule 5: No Spam or Self-Promotion",
                value="No excessive posting, advertising, or self-promotion without permission. Quality over quantity in Victor's realm.",
                inline=False
            )

            rules_embed.add_field(
                name="⚖️ Rule 6: Follow Discord ToS",
                value="All Discord Terms of Service apply. Breaking Discord rules will result in server consequences.",
                inline=False
            )

            rules_embed.add_field(
                name="🔐 Rule 7: Account Security",
                value="Keep your accounts secure. Don't share passwords or personal information. Victor cannot protect the careless.",
                inline=False
            )

            rules_embed.add_field(
                name="✅ **ACCEPT RULES**",
                value="React with ✅ below to accept these rules and gain access to the server. By reacting, you agree to follow all rules and understand that violations may result in warnings, mutes, or permanent bans.",
                inline=False
            )

            rules_embed.set_footer(text="Victor's Domain - Breaking rules has consequences", icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png")

            # Send the rules message
            rules_message = await rules_channel.send(embed=rules_embed)
            
            # Add the checkmark reaction
            await rules_message.add_reaction("✅")

            # Update the bot's rules_message_id
            self.bot.rules_message_id = rules_message.id

            await interaction.followup.send(f"✅ Rules message sent to {rules_channel.mention} with ID: {rules_message.id}")
            logger.info(f"Rules message sent to channel {rules_channel.id} with message ID {rules_message.id}")

        except Exception as e:
            logger.error(f"Error sending rules: {e}")
            await interaction.followup.send("❌ Failed to send rules message", ephemeral=True)

    @app_commands.command(name="send_channel_info", description="Send information embeds to all channels")
    @app_commands.checks.has_role("owner of this house")
    async def send_channel_info(self, interaction: discord.Interaction):
        await interaction.response.defer()

        channel_info = {
            "rules": {
                "title": "📜 Server Rules",
                "description": "React with ✅ to accept the rules and gain access to the server. Please read all rules carefully before proceeding.",
                "color": 0x8B0000
            },
            "announcements": {
                "title": "📢 Server Announcements",
                "description": "Important server updates, events, and announcements will be posted here. Stay informed!",
                "color": 0xFF5FA2
            },
            "new-user-verification": {
                "title": "✅ New User Verification Log",
                "description": "This channel logs all new user verifications. Admins can monitor verification activity here.",
                "color": 0x00FF00
            },
            "item-sales": {
                "title": "🛍️ Item Sales",
                "description": "List your Highrise items for sale here using `/sell item`. Include item name, price, and description.",
                "color": 0x8B0000
            },
            "gold-sales": {
                "title": "💰 Gold Sales",
                "description": "Sell your Highrise gold here using `/sell gold`. Specify amount and total price for transparency.",
                "color": 0xFFD700
            },
            "nft-sales": {
                "title": "🎨 NFT Sales",
                "description": "Trade your Highrise NFTs here using `/sell nft`. Include NFT name, rarity, and asking price.",
                "color": 0x9370DB
            },
            "sold-alerts": {
                "title": "🎯 Sold Alerts",
                "description": "Automated notifications when items are marked as sold. Helps track marketplace activity.",
                "color": 0x32CD32
            },
            "wishlist-requests": {
                "title": "🔍 Wishlist & Requests",
                "description": "Looking for specific items? Post your wishlist and requests here. Other users can help you find what you need!",
                "color": 0xFF69B4
            },
            "interest-pings": {
                "title": "📩 Interest Notifications",
                "description": "When someone shows interest in your listing, notifications appear here for quick seller response.",
                "color": 0x40E0D0
            },
            "art-showcase": {
                "title": "🎨 Art Showcase",
                "description": "Share your Highrise screenshots, outfits, room designs, and artistic creations here!",
                "color": 0xFF6347
            },
            "pets": {
                "title": "🐾 Pet Corner",
                "description": "Show off your real pets or Highrise pets! Share cute photos and pet stories.",
                "color": 0x98FB98
            },
            "selfies": {
                "title": "📸 Selfies & Photos",
                "description": "Share your selfies, photos, and personal moments with the community!",
                "color": 0xFFB6C1
            },
            "memes": {
                "title": "😂 Memes & Humor",
                "description": "Share funny memes, jokes, and humorous content to brighten everyone's day!",
                "color": 0xFFA500
            },
            "venting-zone": {
                "title": "💭 Venting Zone",
                "description": "Need to get something off your chest? This is a safe space for venting and emotional support.",
                "color": 0x6495ED
            },
            "mod-alerts": {
                "title": "🚨 Moderation Alerts",
                "description": "Automated moderation alerts and admin notifications. Staff-only channel for server management.",
                "color": 0xFF0000
            },
            "flagged-listings": {
                "title": "⚠️ Flagged Listings",
                "description": "Suspicious or reported marketplace listings are reviewed here by moderation staff.",
                "color": 0xFF4500
            },
            "logs": {
                "title": "📋 Server Logs",
                "description": "Comprehensive server activity logs including joins, leaves, role changes, and other events.",
                "color": 0x808080
            },
            "giveaway": {
                "title": "🎉 Giveaways",
                "description": "Participate in server giveaways! React to giveaway posts to enter. Good luck!",
                "color": 0x00CED1
            },
            "price-checks": {
                "title": "💎 Price Checks",
                "description": "Unsure about item values? Ask for price checks here to get community input on fair pricing.",
                "color": 0x4169E1
            },
            "victors-vault": {
                "title": "🏛️ Victor's Vault",
                "description": "Exclusive access channel for trusted members, staff, and VIPs. Private discussions and premium features.",
                "color": 0x8B0000
            }
        }

        sent_count = 0
        guild = interaction.guild

        for channel in guild.text_channels:
            if channel.name in channel_info:
                info = channel_info[channel.name]
                
                embed = discord.Embed(
                    title=info["title"],
                    description=info["description"],
                    color=info["color"],
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text="Victor's Channel Guide", icon_url="https://cdn.discordapp.com/emojis/1234567890123456789.png")

                try:
                    await channel.send(embed=embed)
                    sent_count += 1
                    logger.info(f"Sent info embed to #{channel.name}")
                except Exception as e:
                    logger.error(f"Failed to send embed to #{channel.name}: {e}")

        await interaction.followup.send(f"✅ Sent information embeds to {sent_count} channels!")

        logger.info(f"Channel info embeds deployment complete: {sent_count} channels updated")

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