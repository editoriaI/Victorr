"""
Database manager for Victor bot
Handles all database operations and connections
"""

import aiosqlite
import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages all database operations for the bot"""
    
    def __init__(self, db_path: str = "victor_bot.db"):
        self.db_path = db_path
        self.connection = None
        
    async def initialize(self):
        """Initialize database connection and create tables"""
        try:
            self.connection = await aiosqlite.connect(self.db_path)
            await self._create_tables()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                discord_id TEXT UNIQUE NOT NULL,
                discord_username TEXT NOT NULL,
                highrise_username TEXT UNIQUE,
                highrise_user_id TEXT UNIQUE,
                verification_code TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                verified_at TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS guilds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id TEXT UNIQUE NOT NULL,
                guild_name TEXT NOT NULL,
                owner_id TEXT NOT NULL,
                verification_enabled BOOLEAN DEFAULT 1,
                marketplace_enabled BOOLEAN DEFAULT 1,
                welcome_channel TEXT,
                log_channel TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                item_category TEXT NOT NULL,
                price INTEGER NOT NULL,
                description TEXT,
                contact_method TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (seller_id) REFERENCES users (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                buyer_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES listings (id),
                FOREIGN KEY (buyer_id) REFERENCES users (id),
                FOREIGN KEY (seller_id) REFERENCES users (id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS verification_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        ]
        
        for table_sql in tables:
            await self.connection.execute(table_sql)
        
        await self.connection.commit()
    
    async def close(self):
        """Close database connection"""
        if self.connection:
            await self.connection.close()
    
    # User management methods
    async def create_user(self, discord_id: str, discord_username: str) -> int:
        """Create a new user"""
        try:
            cursor = await self.connection.execute(
                "INSERT INTO users (discord_id, discord_username) VALUES (?, ?)",
                (discord_id, discord_username)
            )
            await self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user_by_discord_id(self, discord_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Discord ID"""
        try:
            cursor = await self.connection.execute(
                "SELECT * FROM users WHERE discord_id = ?", (discord_id,)
            )
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Error getting user by Discord ID: {e}")
            return None
    
    async def get_user_by_highrise_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by Highrise username"""
        try:
            cursor = await self.connection.execute(
                "SELECT * FROM users WHERE highrise_username = ?", (username,)
            )
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Error getting user by Highrise username: {e}")
            return None
    
    async def update_user_verification(self, user_id: int, highrise_username: str, 
                                     highrise_user_id: str, verification_code: str) -> bool:
        """Update user verification details"""
        try:
            await self.connection.execute(
                """UPDATE users SET 
                   highrise_username = ?, 
                   highrise_user_id = ?, 
                   verification_code = ?
                   WHERE id = ?""",
                (highrise_username, highrise_user_id, verification_code, user_id)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating user verification: {e}")
            return False
    
    async def verify_user(self, user_id: int) -> bool:
        """Mark user as verified"""
        try:
            await self.connection.execute(
                "UPDATE users SET status = 'verified', verified_at = CURRENT_TIMESTAMP WHERE id = ?",
                (user_id,)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error verifying user: {e}")
            return False
    
    async def get_user_stats(self) -> Dict[str, int]:
        """Get user statistics"""
        try:
            # Total users
            cursor = await self.connection.execute("SELECT COUNT(*) FROM users")
            total = (await cursor.fetchone())[0]
            
            # Verified users
            cursor = await self.connection.execute("SELECT COUNT(*) FROM users WHERE status = 'verified'")
            verified = (await cursor.fetchone())[0]
            
            # Pending users
            cursor = await self.connection.execute("SELECT COUNT(*) FROM users WHERE status = 'pending'")
            pending = (await cursor.fetchone())[0]
            
            return {
                'total': total,
                'verified': verified,
                'pending': pending
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {'total': 0, 'verified': 0, 'pending': 0}
    
    # Listing management methods
    async def create_listing(self, seller_id: int, item_name: str, item_category: str,
                           price: int, description: str, contact_method: str) -> int:
        """Create a new marketplace listing"""
        try:
            cursor = await self.connection.execute(
                """INSERT INTO listings 
                   (seller_id, item_name, item_category, price, description, contact_method)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (seller_id, item_name, item_category, price, description, contact_method)
            )
            await self.connection.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error creating listing: {e}")
            raise
    
    async def get_active_listings(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get active marketplace listings"""
        try:
            cursor = await self.connection.execute(
                """SELECT l.*, u.discord_username, u.highrise_username 
                   FROM listings l 
                   JOIN users u ON l.seller_id = u.id 
                   WHERE l.status = 'active' 
                   ORDER BY l.created_at DESC 
                   LIMIT ? OFFSET ?""",
                (limit, offset)
            )
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting active listings: {e}")
            return []
    
    async def search_listings(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search marketplace listings"""
        try:
            sql = """SELECT l.*, u.discord_username, u.highrise_username 
                     FROM listings l 
                     JOIN users u ON l.seller_id = u.id 
                     WHERE l.status = 'active' AND l.item_name LIKE ?"""
            params = [f"%{query}%"]
            
            if category:
                sql += " AND l.item_category = ?"
                params.append(category)
            
            sql += " ORDER BY l.created_at DESC LIMIT 20"
            
            cursor = await self.connection.execute(sql, params)
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error searching listings: {e}")
            return []
    
    async def get_user_listings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's listings"""
        try:
            cursor = await self.connection.execute(
                "SELECT * FROM listings WHERE seller_id = ? ORDER BY created_at DESC",
                (user_id,)
            )
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            logger.error(f"Error getting user listings: {e}")
            return []
    
    # Guild management methods
    async def add_guild(self, guild_id: str, guild_name: str, owner_id: str) -> bool:
        """Add a new guild"""
        try:
            await self.connection.execute(
                "INSERT OR REPLACE INTO guilds (guild_id, guild_name, owner_id) VALUES (?, ?, ?)",
                (guild_id, guild_name, owner_id)
            )
            await self.connection.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding guild: {e}")
            return False
    
    async def get_guild(self, guild_id: str) -> Optional[Dict[str, Any]]:
        """Get guild by ID"""
        try:
            cursor = await self.connection.execute(
                "SELECT * FROM guilds WHERE guild_id = ?", (guild_id,)
            )
            row = await cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            logger.error(f"Error getting guild: {e}")
            return None
