#!/usr/bin/env python3
"""
Discord Bot for Highrise Metaverse Integration
Main entry point for the bot application
"""

import asyncio
import logging
import os
import sys
import traceback
from datetime import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

from bot.postgres_database import PostgresDatabase
# Removed old menu_system - now using simple_menu only
from bot.welcome_animations import setup_welcome_animations
from bot.utils import create_embed
from bot.colors import Colors, ColoredFormatter, print_banner, print_section
from config import BOT_CONFIG
from keep_alive import keep_alive

class WelcomeView(discord.ui.View):
    """Aesthetic pink-themed welcome buttons"""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="💀 I'm so excited!", style=discord.ButtonStyle.primary, emoji="")
    async def excited_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Excited response button"""
        embed = create_embed(
            "🥰 You're absolutely adorable!",
            f"Aww {interaction.user.mention}, your excitement makes our hearts flutter! 💕\n\n"
            f"We're just as excited to have you here, beautiful! \n\n"
            f"*Keep being your amazing self!* 💀",
            discord.Color.from_rgb(255, 182, 193)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="💀 This is so tolerable!", style=discord.ButtonStyle.success, emoji="💕")
    async def tolerable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cute response button"""
        embed = create_embed(
            "🦋 You have amazing taste!",
            f"Isn't it just the tolerablest, {interaction.user.mention}? 🥺💀\n\n"
            f"We put so much love into making this special for angels like you! \n\n"
            f"*You're going to fit right in, sweetie!* 🌟",
            discord.Color.from_rgb(255, 192, 203)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="😭 I'm emotional", style=discord.ButtonStyle.secondary, emoji="🥺")
    async def emotional_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Emotional/overwhelmed response button"""
        embed = create_embed(
            "🤗 Group hug time!",
            f"Aww honey {interaction.user.mention}, happy tears are the best tears! 🥺💕\n\n"
            f"We're all about those wholesome feels here! You're going to love our little family! 💀\n\n"
            f"*Take your time, we'll be here with virtual hugs!* ",
            discord.Color.from_rgb(255, 182, 193)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🎀 Ready to verify!", style=discord.ButtonStyle.danger, emoji="💀")
    async def ready_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Ready to proceed button"""
        verification_channel = interaction.guild.get_channel(1388813198324666458)
        embed = create_embed(
            "🚀 Let's get you verified, adequate!",
            f"That's the spirit, {interaction.user.mention}! 💀\n\n"
            f"Head over to {verification_channel.mention if verification_channel else '#verification'} and use:\n"
            f"`/verify <your_highrise_username>`\n\n"
            f"*You've got this, superstar!* 🌟",
            discord.Color.from_rgb(255, 105, 180)
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# Load environment variables
load_dotenv()

# Configure colored logging
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Create colored formatter for console
colored_formatter = ColoredFormatter(log_format)

# Create handlers
file_handler = logging.FileHandler('bot.log')
file_handler.setFormatter(logging.Formatter(log_format))

console_handler = logging.StreamHandler()
console_handler.setFormatter(colored_formatter)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

# Reduce logging noise from external libraries
logging.getLogger('werkzeug').setLevel(logging.CRITICAL)
logging.getLogger('discord.client').setLevel(logging.ERROR)
logging.getLogger('discord.gateway').setLevel(logging.ERROR)
logging.getLogger('discord.http').setLevel(logging.ERROR)
logging.getLogger('asyncio').setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

class HighriseBot(commands.Bot):
    """Main bot class with Highrise integration"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=BOT_CONFIG['prefix'],
            intents=intents,
            description="Highrise Metaverse Discord Bot"
        )

        self.db = None
        self.start_time = datetime.now()

    async def setup_hook(self):
        """Setup hook called when bot is starting up"""
        print(Colors.header("🤖 VICTOR BOT STARTUP"))
        
        # Database
        print(Colors.info("🔸 Initializing database..."))
        self.db = PostgresDatabase()
        await self.db.initialize()
        print(Colors.success("✅ Database ready"))

        # Core Systems
        print(Colors.info("🔸 Loading core systems..."))
        await self.load_extension('bot.simple_menu')
        
        await setup_welcome_animations(self)
        
        from bot.help_detector import setup_help_detector
        self.help_detector = await setup_help_detector(self)
        
        from bot.commands import setup
        await setup(self)
        
        from bot.admin_commands import setup_admin_commands
        await setup_admin_commands(self)
        
        from bot.recovery_system import setup_recovery_system
        await setup_recovery_system(self)
        print(Colors.success("✅ All systems loaded"))

        # Discord Sync
        print(Colors.info("🔸 Syncing commands..."))
        try:
            synced = await self.tree.sync()
            print(Colors.success(f"✅ Synced {len(synced)} commands"))
        except Exception as e:
            print(Colors.error(f"❌ Sync failed: {e}"))
            # Continue anyway to avoid hanging

    async def load_message_ids(self):
        """Load critical message IDs from database for crash recovery"""
        try:
            # Load rules message ID
            rules_message_id = await self.db.get_stored_message_id("RULES_MESSAGE_ID")
            if rules_message_id:
                self.rules_message_id = rules_message_id
                logger.info(Colors.success(f"✅ Loaded rules message ID: {self.rules_message_id}"))

            # Load roles message ID
            roles_message_id = await self.db.get_stored_message_id("ROLES_MESSAGE_ID")
            if roles_message_id:
                self.roles_message_id = roles_message_id
                logger.info(Colors.success(f"✅ Loaded roles message ID: {self.roles_message_id}"))

            # Check for missed reactions while bot was offline
            await self.process_missed_reactions()

        except Exception as e:
            logger.error(f"Error loading message IDs: {e}")

    async def process_missed_reactions(self):
        """Process any reactions that were added while bot was offline"""
        try:
            if not hasattr(self, 'rules_message_id') and not hasattr(self, 'roles_message_id'):
                return

            logger.info("Checking for missed reactions while bot was offline...")

            for guild in self.guilds:
                # Process rules message reactions
                if hasattr(self, 'rules_message_id'):
                    await self.check_missed_rules_reactions(guild)

                # Process role message reactions  
                if hasattr(self, 'roles_message_id'):
                    await self.check_missed_role_reactions(guild)

        except Exception as e:
            logger.error(f"Error processing missed reactions: {e}")

    async def check_missed_rules_reactions(self, guild):
        """Check for missed rules reactions and process them"""
        try:
            # Find the rules channel (assuming it's stored in database or config)
            rules_channel_id = 1385445808354365580  # This should be configurable
            rules_channel = guild.get_channel(rules_channel_id)

            if not rules_channel:
                return

            # Get the rules message
            try:
                rules_message = await rules_channel.fetch_message(self.rules_message_id)
            except discord.NotFound:
                logger.warning(f"Rules message {self.rules_message_id} not found")
                return

            # Check reactions on the message
            for reaction in rules_message.reactions:
                if str(reaction.emoji) == "✅":
                    async for user in reaction.users():
                        if user.bot:
                            continue

                        member = guild.get_member(user.id)
                        if not member:
                            continue

                        # Check if user still has unverified role
                        unverified_role = discord.utils.get(guild.roles, name="Unverified")
                        if unverified_role and unverified_role in member.roles:
                            await member.remove_roles(unverified_role, reason="Accepted rules (crash recovery)")
                            logger.info(f"Processed missed rules reaction for {member.name}")

        except Exception as e:
            logger.error(f"Error checking missed rules reactions: {e}")

    async def check_missed_role_reactions(self, guild):
        """Check for missed role reactions and process them"""
        try:
            # Find the roles channel (you may need to adjust this)
            for channel in guild.text_channels:
                try:
                    roles_message = await channel.fetch_message(self.roles_message_id)
                    break
                except discord.NotFound:
                    continue
            else:
                logger.warning(f"Roles message {self.roles_message_id} not found in any channel")
                return

            # Map emojis to role names
            emoji_to_role = {
                "🎯": "Event Notifications",
                "🎁": "Giveaway Notifications", 
                "📚": "Rare Sales Values",
                "⚙️": "Services",
                "🌐": "Room Builder",
                "🎟️": "Raffle Notifications",
                "💰": "Commissions"
            }

            # Check each reaction on the message
            for reaction in roles_message.reactions:
                emoji_str = str(reaction.emoji)
                if emoji_str in emoji_to_role:
                    role_name = emoji_to_role[emoji_str]
                    role = discord.utils.get(guild.roles, name=role_name)

                    if not role:
                        continue

                    async for user in reaction.users():
                        if user.bot:
                            continue

                        member = guild.get_member(user.id)
                        if not member:
                            continue

                        # Add role if they don't have it
                        if role not in member.roles:
                            await member.add_roles(role, reason="Role selection (crash recovery)")
                            logger.info(f"Processed missed role reaction: added {role_name} to {member.name}")

        except Exception as e:
            logger.error(f"Error checking missed role reactions: {e}")

    async def handle_role_reactions(self, payload, member, guild):
        """Handle all types of role reactions"""
        try:
            # Load role message IDs from database
            role_message_ids = {}
            if self.db:
                role_message_ids = {
                    'roles_message_id': await self.db.get_stored_message_id("ROLES_MESSAGE_ID"),
                    'additional_roles_message_id': await self.db.get_stored_message_id("ADDITIONAL_ROLES_MESSAGE_ID"),
                    'pronoun_message_id': await self.db.get_stored_message_id("PRONOUN_MESSAGE_ID"),
                    'identity_message_id': await self.db.get_stored_message_id("IDENTITY_MESSAGE_ID"),
                    'platform_message_id': await self.db.get_stored_message_id("PLATFORM_MESSAGE_ID"),
                    'timezone_message_id': await self.db.get_stored_message_id("TIMEZONE_MESSAGE_ID"),
                    'fandoms_message_id': await self.db.get_stored_message_id("FANDOMS_MESSAGE_ID")
                }

            emoji_str = str(payload.emoji)

            # Notification roles (the proper message ID)
            if role_message_ids.get('additional_roles_message_id') and payload.message_id == int(role_message_ids['additional_roles_message_id']):
                emoji_to_role = {
                    "🎯": "Event Notifications",
                    "📦": "Giveaway Notifications", 
                    "📕": "Rare Sales Values",
                    "⚙️": "Services",
                    "🌐": "Room Builder",
                    "🎟️": "Raffle Notifications",
                    "💸": "Commissions"
                }

                if emoji_str in emoji_to_role:
                    await self.assign_role(member, guild, emoji_to_role[emoji_str], "Notification role selection")

            # Pronoun roles
            elif role_message_ids.get('pronoun_message_id') and payload.message_id == role_message_ids['pronoun_message_id']:
                emoji_to_role = {
                    "⚪": "He/Him",
                    "⚫": "She/Her",
                    "◼️": "They/Them",
                    "✨": "Any Pronouns",
                    "❔": "Ask First"
                }

                if emoji_str in emoji_to_role:
                    await self.assign_role(member, guild, emoji_to_role[emoji_str], "Pronoun role selection")

            # Identity roles
            elif role_message_ids.get('identity_message_id') and payload.message_id == role_message_ids['identity_message_id']:
                emoji_to_role = {
                    "⚫": "Gay",
                    "◻️": "Lesbian",
                    "◼️": "Bisexual",
                    "♦️": "Pansexual",
                    "❄️": "Asexual",
                    "🖤": "Straight",
                    "❔": "Questioning",
                    "🤝": "Ally"
                }

                if emoji_str in emoji_to_role:
                    await self.assign_role(member, guild, emoji_to_role[emoji_str], "Identity role selection")

            # Platform roles
            elif role_message_ids.get('platform_message_id') and payload.message_id == role_message_ids['platform_message_id']:
                emoji_to_role = {
                    "🖥️": "PC",
                    "🎮": "Console",
                    "📱": "Mobile",
                    "💻": "Mac",
                    "🕹️": "VR / Meta"
                }

                if emoji_str in emoji_to_role:
                    await self.assign_role(member, guild, emoji_to_role[emoji_str], "Platform role selection")

            # Timezone roles
            elif role_message_ids.get('timezone_message_id') and payload.message_id == role_message_ids['timezone_message_id']:
                emoji_to_role = {
                    "🌞": "North America (EST/PST)",
                    "🌍": "Europe / UK",
                    "🌏": "Asia / Australia",
                    "🌐": "Other"
                }

                if emoji_str in emoji_to_role:
                    await self.assign_role(member, guild, emoji_to_role[emoji_str], "Timezone role selection")

            # Fandom roles
            elif role_message_ids.get('fandoms_message_id') and payload.message_id == role_message_ids['fandoms_message_id']:
                emoji_to_role = {
                    "🕹️": "Gaming",
                    "💀": "Anime",
                    "🎶": "K-pop",
                    "🧃": "Aesthetic / Fashion",
                    "🎨": "Art",
                    "🎥": "Movies & TV",
                    "📚": "Books"
                }

                if emoji_str in emoji_to_role:
                    await self.assign_role(member, guild, emoji_to_role[emoji_str], "Fandom role selection")

        except Exception as e:
            logger.error(f"Error handling role reactions: {e}")

    async def assign_role(self, member, guild, role_name, reason):
        """Helper method to assign roles"""
        try:
            role = discord.utils.get(guild.roles, name=role_name)

            if role:
                if role not in member.roles:
                    await member.add_roles(role, reason=reason)
                    logger.info(Colors.success(f"✅ Added role {role_name} to {member.name}"))
                else:
                    logger.info(Colors.info(f"ℹ️  Member {member.name} already has role {role_name}"))
            else:
                logger.warning(Colors.warning(f"⚠️  Role {role_name} not found in guild {guild.name}"))
        except Exception as e:
            logger.error(Colors.error(f"❌ Error assigning role {role_name}: {e}"))

    async def on_ready(self):
        """Event triggered when bot is ready"""
        # Set start time for uptime calculation
        self.start_time = datetime.now()

        print(Colors.success(f"✅ Connected as {self.user}"))
        total_members = sum(g.member_count or 0 for g in self.guilds)
        print(Colors.info(f"📊 {len(self.guilds)} servers | {total_members} members"))
        
        # Set bot status
        activity = discord.Activity(type=discord.ActivityType.watching, name="Highrise Metaverse")
        await self.change_presence(activity=activity)
        
        print(Colors.header("🚀 Victor is now online and ready!"))

    async def on_message(self, message):
        """Process messages with Victor's intelligent help detection"""
        if message.author.bot:
            return

        # Log all messages that start with the command prefix for debugging
        if message.content.startswith(self.command_prefix):
            logger.info(f"Command attempt: '{message.content}' by {message.author.name} in {message.guild.name if message.guild else 'DM'}")

        # Victor's intelligent help detection (skip for ALL commands to avoid conflicts)
        if hasattr(self, 'help_detector') and message.guild and not message.content.startswith(self.command_prefix):
            try:
                help_response = await self.help_detector.analyze_message(message)
                if help_response:
                    await self.help_detector.send_help_suggestion(message, help_response)
            except Exception as e:
                logger.error(f"Victor's help detection error: {e}")

        await self.process_commands(message)

    async def on_member_join(self, member):
        """Lock new members until they react to rules"""
        try:
            guild = member.guild

            # Only apply to hr blacklist server, ignore toybox
            if guild.name == "「 ✦ Toy Box ✦ 」":
                logger.info(f"Ignoring member join in Toy Box server: {member.name}")
                return

            # Create a role that restricts access (if it doesn't exist)
            unverified_role = discord.utils.get(guild.roles, name="Unverified")

            if not unverified_role:
                # Create the unverified role with restricted permissions
                unverified_role = await guild.create_role(
                    name="Unverified",
                    permissions=discord.Permissions(read_messages=True, read_message_history=True),
                    reason="Role for new members who haven't accepted rules"
                )

                # Apply role restrictions to all channels except rules channel
                for channel in guild.channels:
                    if channel.id != 1385445808354365580:  # Rules channel ID
                        await channel.set_permissions(unverified_role, view_channel=False)
                    else:
                        await channel.set_permissions(unverified_role, view_channel=True, send_messages=False, add_reactions=True)

            # Assign the unverified role to new member
            await member.add_roles(unverified_role, reason="New member - requires rule acceptance")

            logger.info(Colors.info(f"👤 New member {member.name} joined and was given Unverified role"))

            # Start welcome animation sequence
            if hasattr(self, 'welcome_animator'):
                logger.info(Colors.info(f"🎬 Starting welcome animation for {member.name}"))
                asyncio.create_task(self.welcome_animator.play_welcome_animation(member))

        except Exception as e:
            logger.error(f"Error handling new member {member.name}: {e}")

    async def on_raw_reaction_add(self, payload):
        """Handle reactions to rules message and role selection"""
        try:
            # Get the member and guild
            guild = self.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)

            # Ignore bot reactions
            if not member or member.bot:
                return

            # Handle rules message reactions
            if hasattr(self, 'rules_message_id') and payload.message_id == self.rules_message_id:
                # Check if reaction is the checkmark
                if str(payload.emoji) != "✅":
                    return

                # Remove unverified role and allow access to verification channel
                unverified_role = discord.utils.get(guild.roles, name="Unverified")
                if unverified_role and unverified_role in member.roles:
                    await member.remove_roles(unverified_role, reason="Accepted rules")

                    # Send tolerable welcome message to welcome channel
                    welcome_channel = self.get_channel(1385446898608898200)
                    verification_channel = self.get_channel(1388813198324666458)

                    if welcome_channel:
                        embed = create_embed(
                            " Welcome to Our Magical Space! ",
                            f"Hey adequate {member.mention}! 💕\n\n"
                            f"Thank you for reading our rules — you're absolutely amazing! \n\n"
                            f"**Your next steps are super easy:**\n"
                            f"✅ **1. Read the rules** — *already done, you cutie!*\n"
                            f"💀 **2. Head to {verification_channel.mention}** and use `/verify <your_highrise_username>`\n"
                            f"💀 **3. Get verified and start your adventure with us!**\n\n"
                            f"*We can't wait to see you shine in our community!* 🌟\n\n"
                            f"💭 *How are you feeling about joining us?*",
                            discord.Color.from_rgb(255, 182, 193)  # Light pink
                        )

                        # Add efficient footer
                        embed.set_footer(text="💕 Click a button below to share your vibes! 💕")

                        # Create the tolerable button view
                        view = WelcomeView()

                        await welcome_channel.send(embed=embed, view=view)

                    logger.info(f"Member {member.name} accepted rules and can now access verification")

            # Handle role selection reactions
            else:
                # Check for all different role message types
                await self.handle_role_reactions(payload, member, guild)

        except Exception as e:
            logger.error(f"Error handling reaction: {e}")

    

    async def handle_role_removal(self, payload, member, guild):
        """Handle removal of all types of role reactions"""
        try:
            # Load role message IDs from database
            role_message_ids = {}
            if self.db:
                role_message_ids = {
                    'roles_message_id': await self.db.get_stored_message_id("ROLES_MESSAGE_ID"),
                    'additional_roles_message_id': await self.db.get_stored_message_id("ADDITIONAL_ROLES_MESSAGE_ID"),
                    'pronoun_message_id': await self.db.get_stored_message_id("PRONOUN_MESSAGE_ID"),
                    'identity_message_id': await self.db.get_stored_message_id("IDENTITY_MESSAGE_ID"),
                    'platform_message_id': await self.db.get_stored_message_id("PLATFORM_MESSAGE_ID"),
                    'timezone_message_id': await self.db.get_stored_message_id("TIMEZONE_MESSAGE_ID"),
                    'fandoms_message_id': await self.db.get_stored_message_id("FANDOMS_MESSAGE_ID")
                }

            emoji_str = str(payload.emoji)

            # Notification roles (the proper message ID)
            if role_message_ids.get('additional_roles_message_id') and payload.message_id == int(role_message_ids['additional_roles_message_id']):
                emoji_to_role = {
                    "🎯": "Event Notifications",
                    "📦": "Giveaway Notifications", 
                    "📕": "Rare Sales Values",
                    "⚙️": "Services",
                    "🌐": "Room Builder",
                    "🎟️": "Raffle Notifications",
                    "💸": "Commissions"
                }

                if emoji_str in emoji_to_role:
                    await self.remove_role(member, guild, emoji_to_role[emoji_str], "Notification role removal")

            # Pronoun roles
            elif role_message_ids.get('pronoun_message_id') and payload.message_id == role_message_ids['pronoun_message_id']:
                emoji_to_role = {
                    "⚪": "He/Him",
                    "⚫": "She/Her",
                    "◼️": "They/Them",
                    "✨": "Any Pronouns",
                    "❔": "Ask First"
                }

                if emoji_str in emoji_to_role:
                    await self.remove_role(member, guild, emoji_to_role[emoji_str], "Pronoun role removal")

            # Identity roles
            elif role_message_ids.get('identity_message_id') and payload.message_id == role_message_ids['identity_message_id']:
                emoji_to_role = {
                    "⚫": "Gay",
                    "◻️": "Lesbian",
                    "◼️": "Bisexual",
                    "♦️": "Pansexual",
                    "❄️": "Asexual",
                    "🖤": "Straight",
                    "❔": "Questioning",
                    "🤝": "Ally"
                }

                if emoji_str in emoji_to_role:
                    await self.remove_role(member, guild, emoji_to_role[emoji_str], "Identity role removal")

            # Platform roles
            elif role_message_ids.get('platform_message_id') and payload.message_id == role_message_ids['platform_message_id']:
                emoji_to_role = {
                    "🖥️": "PC",
                    "🎮": "Console",
                    "📱": "Mobile",
                    "💻": "Mac",
                    "🕹️": "VR / Meta"
                }

                if emoji_str in emoji_to_role:
                    await self.remove_role(member, guild, emoji_to_role[emoji_str], "Platform role removal")

            # Timezone roles
            elif role_message_ids.get('timezone_message_id') and payload.message_id == role_message_ids['timezone_message_id']:
                emoji_to_role = {
                    "🌞": "North America (EST/PST)",
                    "🌍": "Europe / UK",
                    "🌏": "Asia / Australia",
                    "🌐": "Other"
                }

                if emoji_str in emoji_to_role:
                    await self.remove_role(member, guild, emoji_to_role[emoji_str], "Timezone role removal")

            # Fandom roles
            elif role_message_ids.get('fandoms_message_id') and payload.message_id == role_message_ids['fandoms_message_id']:
                emoji_to_role = {
                    "🕹️": "Gaming",
                    "💀": "Anime",
                    "🎶": "K-pop",
                    "🧃": "Aesthetic / Fashion",
                    "🎨": "Art",
                    "🎥": "Movies & TV",
                    "📚": "Books"
                }

                if emoji_str in emoji_to_role:
                    await self.remove_role(member, guild, emoji_to_role[emoji_str], "Fandom role removal")

        except Exception as e:
            logger.error(f"Error handling role removal: {e}")

    async def remove_role(self, member, guild, role_name, reason):
        """Helper method to remove roles"""
        try:
            role = discord.utils.get(guild.roles, name=role_name)

            if role and role in member.roles:
                await member.remove_roles(role, reason=reason)
                logger.info(Colors.warning(f"🗑️ Removed role {role_name} from {member.name}"))
            else:
                logger.info(Colors.debug(f"🔍 Member {member.name} doesn't have role {role_name} to remove"))
        except Exception as e:
            logger.error(Colors.error(f"❌ Error removing role {role_name}: {e}"))

    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ Command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
        else:
            logger.error(f"Command error in {ctx.command}: {error}")
            await ctx.send("❌ An unexpected error occurred. Please try again later.")

    async def close(self):
        """Cleanup when bot is shutting down"""
        logger.info("Bot is shutting down...")
        if self.db:
            await self.db.close()
        await super().close()

def validate_environment():
    """Validate required environment variables"""
    required_vars = ['DISCORD_BOT_TOKEN']
    optional_vars = ['HIGHRISE_API_KEY', 'SESSION_SECRET']

    missing_required = []
    missing_optional = []

    print_section("Environment Validation", "Checking required environment variables...")

    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_required.append(var)
            print(Colors.error(f"❌ Missing required: {var}"))
        else:
            print(Colors.success(f"✅ Found: {var}"))

    for var in optional_vars:
        value = os.getenv(var)
        if not value:
            missing_optional.append(var)
            print(Colors.warning(f"⚠️  Missing optional: {var}"))
        else:
            print(Colors.success(f"✅ Found: {var}"))

    if missing_required:
        print(Colors.error(f"\n💀 Cannot start bot - missing required environment variables: {', '.join(missing_required)}"))
        print(Colors.info("💡 Please add the required environment variables in your deployment secrets"))
        return False

    if missing_optional:
        print(Colors.warning(f"\n⚠️  Optional variables not set: {', '.join(missing_optional)}"))
        print(Colors.info("💡 Some features may be limited without these variables"))

    return True

async def run_bot_with_restart():
    """Run the bot with automatic restart on crash"""
    max_retries = 5
    retry_count = 0
    base_delay = 5  # Initial delay in seconds

    print_banner("🔄 BOT STARTUP WITH AUTO-RESTART")

    # Validate environment variables before starting
    if not validate_environment():
        return

    while retry_count < max_retries:
        try:
            print(Colors.info(f"🚀 Starting bot (attempt {Colors.colorize(str(retry_count + 1), Colors.BRIGHT_YELLOW, bold=True)}/{max_retries})"))

            # Get Discord token from environment (already validated)
            token = os.getenv('DISCORD_BOT_TOKEN')
            if not token:  # Additional safety check
                print(Colors.error("❌ DISCORD_BOT_TOKEN not found"))
                break

            print(Colors.success("✅ Discord token found"))
            print(Colors.info("🔌 Connecting to Discord..."))

            # Create and run bot
            bot = HighriseBot()
            await bot.start(token)

        except KeyboardInterrupt:
            print(Colors.warning("⚠️  Received interrupt signal - shutting down gracefully"))
            break

        except discord.LoginFailure as e:
            print(Colors.error("❌ Invalid bot token - cannot restart"))
            print(Colors.info("💡 Please check your DISCORD_BOT_TOKEN in the deployment secrets"))
            logger.error(f"Login failure: {e}")
            break

        except discord.HTTPException as e:
            print(Colors.error(f"❌ Discord HTTP error: {e}"))
            logger.error(f"Discord HTTP error: {e}")
            retry_count += 1
            if retry_count < max_retries:
                delay = base_delay * (2 ** (retry_count - 1))
                print(Colors.warning(f"⏳ Retrying in {delay} seconds... (attempt {retry_count + 1}/{max_retries})"))
                await asyncio.sleep(delay)
            else:
                print(Colors.error("💀 Max restart attempts reached. Bot will not restart."))
                break

        except discord.ConnectionClosed as e:
            print(Colors.warning(f"⚠️  Connection closed: {e}"))
            logger.warning(f"Connection closed: {e}")
            retry_count += 1
            if retry_count < max_retries:
                delay = base_delay
                print(Colors.warning(f"⏳ Reconnecting in {delay} seconds... (attempt {retry_count + 1}/{max_retries})"))
                await asyncio.sleep(delay)
            else:
                print(Colors.error("💀 Max restart attempts reached. Bot will not restart."))
                break

        except Exception as e:
            retry_count += 1
            delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff

            print(Colors.error(f"💥 Bot crashed with error: {e}"))
            logger.error(f"Traceback: {traceback.format_exc()}")

            # Log additional context for debugging
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error args: {e.args}")

            if retry_count < max_retries:
                print(Colors.warning(f"⏳ Restarting in {Colors.colorize(str(delay), Colors.BRIGHT_YELLOW, bold=True)} seconds... (attempt {retry_count + 1}/{max_retries})"))
                await asyncio.sleep(delay)
            else:
                print(Colors.error("💀 Max restart attempts reached. Bot will not restart."))
                break

        finally:
            # Ensure cleanup happens
            try:
                if 'bot' in locals():
                    print(Colors.info("🧹 Cleaning up bot resources..."))
                    await bot.close()
            except:
                pass

async def main():
    """Main function to run the bot with restart capability"""
    # Start the keep-alive server for port availability
    keep_alive()
    await run_bot_with_restart()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Colors.warning("👋 Bot stopped by user"))
    except Exception as e:
        print(Colors.error(f"💀 Fatal error: {e}"))
        sys.exit(1)