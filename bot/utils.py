"""
Utility functions for Victor bot
Helper functions and shared utilities
"""

import aiohttp
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class HighriseAPI:
    """Highrise Web API integration"""
    
    BASE_URL = "https://webapi.highrise.game"
    
    @classmethod
    async def get_user_by_username(cls, username: str) -> Optional[Dict[str, Any]]:
        """Get user data by username with bio information"""
        try:
            # First, search for the user (case-insensitive)
            search_url = f"{cls.BASE_URL}/users"
            search_params = {"username": username.lower()}
            headers = {
                'User-Agent': 'Victor-Discord-Bot/1.0',
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                # Search for user
                async with session.get(search_url, params=search_params, headers=headers, 
                                     timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'users' in data and data['users']:
                            # Find exact match (case-insensitive)
                            for user in data['users']:
                                if user.get('username', '').lower() == username.lower():
                                    user_id = user.get('user_id')
                                    if user_id:
                                        # Now get full profile with bio
                                        return await cls._get_user_profile_with_bio(user_id, session, headers)
                    
                    logger.warning(f"User {username} not found in search results")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Highrise user {username}: {e}")
            return None
    
    @classmethod
    async def _get_user_profile_with_bio(cls, user_id: str, session: aiohttp.ClientSession, headers: dict) -> Optional[Dict[str, Any]]:
        """Get user profile with bio data"""
        try:
            # Try the profile endpoint for bio data
            profile_url = f"{cls.BASE_URL}/users/{user_id}"
            async with session.get(profile_url, headers=headers, 
                                 timeout=aiohttp.ClientTimeout(total=15)) as response:
                if response.status == 200:
                    profile_data = await response.json()
                    logger.info(f"Successfully retrieved profile for user {user_id}")
                    return profile_data
                else:
                    logger.warning(f"Failed to get profile for user {user_id}: Status {response.status}")
            
            # If profile endpoint doesn't work, try alternative endpoints
            alt_endpoints = [
                f"{cls.BASE_URL}/users/{user_id}/profile",
                f"{cls.BASE_URL}/users/{user_id}/info",
                f"{cls.BASE_URL}/user/{user_id}",
                f"{cls.BASE_URL}/profile/{user_id}"
            ]
            
            for endpoint in alt_endpoints:
                try:
                    async with session.get(endpoint, headers=headers, 
                                         timeout=aiohttp.ClientTimeout(total=10)) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"Successfully retrieved data from {endpoint}")
                            return data
                        else:
                            logger.debug(f"Endpoint {endpoint} returned status {response.status}")
                except Exception as e:
                    logger.debug(f"Error trying endpoint {endpoint}: {e}")
                    continue
            
            logger.warning(f"Could not retrieve bio data for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile with bio: {e}")
            return None
    
    @classmethod
    async def get_user_by_id(cls, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by user ID"""
        try:
            url = f"{cls.BASE_URL}/users/{user_id}"
            headers = {
                'User-Agent': 'Victor-Discord-Bot/1.0',
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, 
                                     timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        return await response.json()
                    
                    logger.warning(f"Failed to get user ID {user_id}: Status {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Highrise user ID {user_id}: {e}")
            return None
    
    @classmethod
    async def search_items(cls, query: str, category: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search marketplace items"""
        try:
            url = f"{cls.BASE_URL}/items"
            params = {"name": query, "limit": limit}
            
            if category:
                params["category"] = category
            
            headers = {
                'User-Agent': 'Victor-Discord-Bot/1.0',
                'Accept': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, 
                                     timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', [])
                    
                    logger.warning(f"Failed to search items: Status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching items: {e}")
            return []

def format_price(price: int) -> str:
    """Format price with commas"""
    return f"{price:,}"

def format_datetime(dt: datetime) -> str:
    """Format datetime for display"""
    return dt.strftime("%Y-%m-%d %H:%M UTC")

def get_relative_time(dt: datetime) -> str:
    """Get relative time string"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

def validate_highrise_username(username: str) -> bool:
    """Validate Highrise username format"""
    if not username or len(username) < 3 or len(username) > 20:
        return False
    
    # Basic validation - alphanumeric and underscores
    return username.replace('_', '').isalnum()

def generate_verification_code(length: int = 6) -> str:
    """Generate a random verification code"""
    import random
    import string
    
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 60, window: int = 60):
        self.max_calls = max_calls
        self.window = window
        self.calls = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if a call is allowed for the given key"""
        now = datetime.utcnow()
        
        if key not in self.calls:
            self.calls[key] = []
        
        # Remove old calls outside the window
        self.calls[key] = [call_time for call_time in self.calls[key] 
                          if (now - call_time).seconds < self.window]
        
        # Check if under limit
        if len(self.calls[key]) < self.max_calls:
            self.calls[key].append(now)
            return True
        
        return False

# Global rate limiter instance
api_rate_limiter = RateLimiter(max_calls=60, window=60)

def log_user_activity(user_id: str, action: str, details: Dict[str, Any] = None):
    """Log user activity"""
    logger.info(f"User {user_id} performed action: {action}")
    if details:
        logger.debug(f"Action details: {details}")

class EmbedBuilder:
    """Helper class for building Discord embeds"""
    
    @staticmethod
    def success(title: str, description: str) -> dict:
        """Create a success embed"""
        return {
            "title": f"✅ {title}",
            "description": description,
            "color": 0x00FF00
        }
    
    @staticmethod
    def error(title: str, description: str) -> dict:
        """Create an error embed"""
        return {
            "title": f"❌ {title}",
            "description": description,
            "color": 0xFF0000
        }
    
    @staticmethod
    def info(title: str, description: str) -> dict:
        """Create an info embed"""
        return {
            "title": f"ℹ️ {title}",
            "description": description,
            "color": 0xFF5FA2
        }
    
    @staticmethod
    def warning(title: str, description: str) -> dict:
        """Create a warning embed"""
        return {
            "title": f"⚠️ {title}",
            "description": description,
            "color": 0xFFAA00
        }

def sanitize_input(text: str, max_length: int = 200) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially harmful characters
    sanitized = text.replace('@', '').replace('`', '').replace('\n', ' ')
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length-3] + "..."
    
    return sanitized.strip()

def is_valid_discord_id(discord_id: str) -> bool:
    """Validate Discord ID format"""
    try:
        int(discord_id)
        return len(discord_id) >= 17 and len(discord_id) <= 20
    except ValueError:
        return False

def format_user_display(discord_username: str, highrise_username: str = None) -> str:
    """Format user display name"""
    if highrise_username:
        return f"{discord_username} ({highrise_username})"
    return discord_username
