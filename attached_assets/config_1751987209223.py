"""
Configuration settings for the Highrise Discord bot
Centralized configuration management
"""

import os
from typing import Dict, Any

# Bot configuration
BOT_CONFIG = {
    'prefix': '-',
    'description': 'Highrise Metaverse Discord Bot',
    'version': '1.0.0',
    'author': 'Highrise Bot Team'
}

# Database configuration
DATABASE_CONFIG = {
    'path': 'highrise_bot.db',
    'backup_interval': 3600,  # seconds
    'max_connections': 10
}

# API configuration
API_CONFIG = {
    'highrise_base_url': 'https://webapi.highrise.game',
    'request_timeout': 30,
    'rate_limit_delay': 1.0,
    'max_retries': 3
}

# Market configuration
MARKET_CONFIG = {
    'max_price': 1000000000,  # 1 billion coins
    'min_price': 1,
    'max_listings_per_user': 10,
    'listing_duration_days': 30,
    'transaction_fee_rate': 0.05,  # 5% fee
    'categories': [
        'Clothing',
        'Furniture',
        'Accessories',
        'Pets',
        'Emotes',
        'Miscellaneous'
    ]
}

# Security configuration
SECURITY_CONFIG = {
    'max_item_name_length': 100,
    'max_description_length': 500,
    'rate_limit_attempts': 5,
    'rate_limit_window': 60,  # seconds
    'admin_user_ids': [
        # Add admin Discord user IDs here
    ]
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file_path': 'bot.log',
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# Discord embed colors
EMBED_COLORS = {
    'success': 0x00ff00,
    'error': 0xff0000,
    'warning': 0xffff00,
    'info': 0x0099ff,
    'market': 0x9932cc,
    'transaction': 0xffd700
}

# Environment variables with defaults
def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables"""
    return {
        'DISCORD_BOT_TOKEN': os.getenv('DISCORD_BOT_TOKEN', ''),
        'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
        'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'DATABASE_PATH': os.getenv('DATABASE_PATH', 'highrise_bot.db'),
        'MAX_GUILDS': int(os.getenv('MAX_GUILDS', '100')),
        'ADMIN_GUILD_ID': os.getenv('ADMIN_GUILD_ID', ''),
    }

# Command cooldowns (in seconds)
COMMAND_COOLDOWNS = {
    'verify': 300,      # 5 minutes
    'list': 60,         # 1 minute
    'buy': 30,          # 30 seconds
    'market': 10,       # 10 seconds
    'help': 5,          # 5 seconds
    'status': 30        # 30 seconds
}

# Feature flags
FEATURES = {
    'verification_required': True,
    'transaction_fees': True,
    'rate_limiting': True,
    'logging': True,
    'admin_commands': True,
    'user_stats': True,
    'market_analytics': False  # Disabled for initial release
}

# Error messages
ERROR_MESSAGES = {
    'not_verified': "You must verify your Highrise account first. Use `/verify <username>` to get started!",
    'api_error': "There was an error communicating with the Highrise API. Please try again later.",
    'database_error': "Database error occurred. Please contact an administrator.",
    'invalid_item': "Invalid item name or format. Please check your input.",
    'insufficient_funds': "You don't have enough coins for this transaction.",
    'item_not_found': "The requested item could not be found.",
    'listing_not_found': "The listing you're looking for doesn't exist or has been removed.",
    'permission_denied': "You don't have permission to perform this action.",
    'rate_limited': "You're being rate limited. Please wait before trying again.",
    'server_error': "An internal server error occurred. Please try again later."
}

# Success messages
SUCCESS_MESSAGES = {
    'verification_complete': "Successfully verified your Highrise account!",
    'item_listed': "Your item has been listed on the black market!",
    'purchase_complete': "Purchase successful! The item should appear in your inventory soon.",
    'listing_removed': "Your listing has been removed from the market.",
    'transaction_complete': "Transaction completed successfully!"
}

# Validation rules
VALIDATION_RULES = {
    'username': {
        'min_length': 3,
        'max_length': 50,
        'allowed_chars': r'^[a-zA-Z0-9_-]+$'
    },
    'item_name': {
        'min_length': 1,
        'max_length': 100,
        'forbidden_chars': r'[<>@&]'
    },
    'description': {
        'max_length': 500
    },
    'price': {
        'min_value': 1,
        'max_value': 1000000000
    }
}

# Default bot status messages
STATUS_MESSAGES = [
    "Watching Highrise Metaverse",
    "Managing the black market",
    "Helping users trade items",
    f"Version {BOT_CONFIG['version']}",
    "Type /help for commands"
]

def validate_config():
    """Validate configuration on startup"""
    env_config = get_env_config()
    
    if not env_config['DISCORD_BOT_TOKEN']:
        raise ValueError("DISCORD_BOT_TOKEN is required")
    
    return True

# Export all configurations
__all__ = [
    'BOT_CONFIG',
    'DATABASE_CONFIG', 
    'API_CONFIG',
    'MARKET_CONFIG',
    'SECURITY_CONFIG',
    'LOGGING_CONFIG',
    'EMBED_COLORS',
    'COMMAND_COOLDOWNS',
    'FEATURES',
    'ERROR_MESSAGES',
    'SUCCESS_MESSAGES',
    'VALIDATION_RULES',
    'STATUS_MESSAGES',
    'get_env_config',
    'validate_config'
]
