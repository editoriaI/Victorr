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
from bot.commands import setup_commands
from keep_alive import keep_alive

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

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
        logger.info("Setting up bot...")
        
        try:
            # Initialize database
            self.db = DatabaseManager()
            await self.db.initialize()
            logger.info("Database initialized successfully")
            
            # Setup commands
            await setup_commands(self)
            logger.info("All command cogs loaded successfully")
            
            # Sync commands
            logger.info("Starting command sync...")
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
            
        except Exception as e:
            logger.error(f"Error during bot setup: {e}")
            raise
    
    async def on_ready(self):
        """Bot ready event"""
        logger.info(f"{self.user} has connected to Discord!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        self.startup_complete = True
        
        # Set presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="the Highrise marketplace"
            )
        )
    
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
