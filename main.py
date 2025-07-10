#!/usr/bin/env python3
"""
Victor - Discord Bot for Highrise Trading
Main entry point that starts both the Discord bot and Flask web app
"""

import asyncio
import logging
import os
import threading
import signal
import sys
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from bot.database import DatabaseManager
from bot.commands import setup_commands, SellView
from keep_alive import keep_alive

# Load environment variables
load_dotenv()

# Color codes for console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    PURPLE = '\033[35m'
    YELLOW = '\033[33m'

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    FORMATS = {
        logging.DEBUG: Colors.OKCYAN + "🔧 DEBUG" + Colors.ENDC + " - %(name)s - %(message)s",
        logging.INFO: Colors.OKGREEN + "✅ INFO" + Colors.ENDC + " - %(name)s - %(message)s", 
        logging.WARNING: Colors.WARNING + "⚠️  WARN" + Colors.ENDC + " - %(name)s - %(message)s",
        logging.ERROR: Colors.FAIL + "❌ ERROR" + Colors.ENDC + " - %(name)s - %(message)s",
        logging.CRITICAL: Colors.FAIL + Colors.BOLD + "💀 CRITICAL" + Colors.ENDC + " - %(name)s - %(message)s"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self._style._fmt)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Configure colored logging
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())

file_handler = logging.FileHandler('bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

# Reduce noise from external libraries
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('discord.client').setLevel(logging.WARNING)
logging.getLogger('discord.gateway').setLevel(logging.WARNING)
logging.getLogger('discord.http').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class VictorBot(commands.Bot):
    """Victor - The Discord Bot for Highrise Trading"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True

        super().__init__(
            command_prefix='!',
            intents=intents,
            help_command=None,
            description="Victor - Your Highrise Trading Assistant"
        )

        self.db = None
        self.startup_complete = False

    async def setup_hook(self):
        """Initialize bot components"""
        print(f"\n{Colors.PURPLE}{'='*50}")
        print(f"🏴‍☠️  VICTOR BOT STARTUP SEQUENCE")
        print(f"{'='*50}{Colors.ENDC}\n")
        
        logger.info("Victor is awakening from his eternal slumber...")

        try:
            # Initialize database
            logger.info("Setting up the crypt (database)...")
            self.db = DatabaseManager()
            await self.db.initialize()
            logger.info("The crypt is ready for business!")

            # Setup commands
            logger.info("Loading Victor's arsenal of commands...")
            await setup_commands(self)
            logger.info("All weapons loaded and ready!")

            # Add persistent views for marketplace buttons
            logger.info("Setting up persistent marketplace views...")
            self.add_view(SellView(0, "placeholder", "placeholder"))
            logger.info("Marketplace is ready for dark dealings!")

            # Sync commands
            logger.info("Synchronizing with Discord's realm...")
            synced = await self.tree.sync()
            logger.info(f"Successfully registered {len(synced)} slash commands!")

            print(f"\n{Colors.OKGREEN}✨ Victor is fully operational! ✨{Colors.ENDC}")

        except Exception as e:
            logger.error(f"Victor's awakening failed: {e}")
            print(f"\n{Colors.FAIL}💀 STARTUP FAILED 💀{Colors.ENDC}")
            raise

    async def on_ready(self):
        """Bot ready event"""
        print(f"\n{Colors.HEADER}{'='*60}")
        print(f"💀 VICTOR HAS RISEN! 💀")
        print(f"{'='*60}{Colors.ENDC}")
        
        logger.info(f"Victor ({self.user}) has materialized in Discord!")
        logger.info(f"Currently haunting {len(self.guilds)} server(s)")
        
        for guild in self.guilds:
            logger.info(f"  👻 {guild.name} (ID: {guild.id}) - {guild.member_count} souls")
        
        self.startup_complete = True

        # Set presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the Highrise blacklist"
            )
        )
        
        print(f"\n{Colors.BOLD}{Colors.PURPLE}Victor is now watching... Always watching...{Colors.ENDC}\n")

    async def on_guild_join(self, guild):
        """Handle joining a new guild"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")

        # Send welcome message to system channel if available
        if guild.system_channel:
            embed = discord.Embed(
                title="👋 Victor has arrived!",
                description=(
                    "Thank you for inviting me to your server!\n\n"
                    "I'm Victor, your Highrise trading assistant. I can help with:\n"
                    "• User verification through Highrise profiles\n"
                    "• Marketplace for item trading\n"
                    "• Server management tools\n\n"
                    "Use `/help` to get started or visit my web dashboard!"
                ),
                color=0xFF5FA2
            )
            embed.set_footer(text="Victor - Highrise Trading Bot")

            try:
                await guild.system_channel.send(embed=embed)
            except discord.Forbidden:
                logger.warning(f"Could not send welcome message to {guild.name}")

    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return

        logger.error(f"Command error in {ctx.command}: {error}")

        embed = discord.Embed(
            title="❌ Error",
            description="Something went wrong. Please try again later.",
            color=0xFF0000
        )

        try:
            await ctx.send(embed=embed, ephemeral=True)
        except:
            pass

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal. Cleaning up...")
    sys.exit(0)

async def main():
    """Main bot function"""
    # Check for Discord token
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.error("DISCORD_BOT_TOKEN not found in environment variables")
        return

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start web app in separate thread
    keep_alive()

    # Create and run bot
    bot = VictorBot()

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested")
    except Exception as e:
        logger.error(f"Bot error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)