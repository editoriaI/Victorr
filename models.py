from app import db
from datetime import datetime
import enum

class UserStatus(enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    BANNED = "banned"

class ListingStatus(enum.Enum):
    ACTIVE = "active"
    SOLD = "sold"
    CANCELLED = "cancelled"

class TransactionStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(20), unique=True, nullable=False)
    discord_username = db.Column(db.String(100), nullable=False)
    highrise_username = db.Column(db.String(100), unique=True, nullable=True)
    highrise_user_id = db.Column(db.String(50), unique=True, nullable=True)
    verification_code = db.Column(db.String(10), nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # Use string to match bot database
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New fields for enhanced features
    reputation_score = db.Column(db.Float, default=0.0)
    total_trades = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text, nullable=True)
    avatar_url = db.Column(db.String(500), nullable=True)
    is_premium = db.Column(db.Boolean, default=False)
    referred_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    listings = db.relationship('Listing', backref='seller', lazy=True, cascade='all, delete-orphan')
    transactions_as_buyer = db.relationship('Transaction', foreign_keys='Transaction.buyer_id', backref='buyer', lazy=True)
    transactions_as_seller = db.relationship('Transaction', foreign_keys='Transaction.seller_id', backref='seller', lazy=True)
    wishlists = db.relationship('Wishlist', backref='user', lazy=True, cascade='all, delete-orphan')
    reviews_given = db.relationship('Review', foreign_keys='Review.reviewer_id', backref='reviewer', lazy=True)
    reviews_received = db.relationship('Review', foreign_keys='Review.reviewee_id', backref='reviewee', lazy=True)
    
    def __repr__(self):
        return f'<User {self.discord_username}>'

class Guild(db.Model):
    __tablename__ = 'guilds'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(20), unique=True, nullable=False)
    guild_name = db.Column(db.String(200), nullable=False)
    owner_id = db.Column(db.String(20), nullable=False)
    verification_enabled = db.Column(db.Boolean, default=True)
    marketplace_enabled = db.Column(db.Boolean, default=True)
    welcome_channel = db.Column(db.String(20), nullable=True)
    log_channel = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Guild {self.guild_name}>'

class Listing(db.Model):
    __tablename__ = 'listings'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    item_category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)  # Price in coins
    description = db.Column(db.Text, nullable=True)
    contact_method = db.Column(db.String(200), nullable=False)  # Discord, Highrise, etc.
    status = db.Column(db.String(20), default='active', nullable=False)  # Use string instead of enum to match bot
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # New fields for enhanced features
    condition = db.Column(db.String(50), default='Good', nullable=False)  # New, Like New, Good, Fair
    is_featured = db.Column(db.Boolean, default=False)
    views = db.Column(db.Integer, default=0)
    favorites = db.Column(db.Integer, default=0)
    images = db.Column(db.JSON, nullable=True)  # Array of image URLs
    tags = db.Column(db.JSON, nullable=True)  # Array of searchable tags
    original_price = db.Column(db.Integer, nullable=True)  # For price history
    negotiable = db.Column(db.Boolean, default=True)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='listing', lazy=True)
    
    def __repr__(self):
        return f'<Listing {self.item_name}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id'), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Transaction {self.id}>'

class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    discord_id = db.Column(db.String(20), unique=True, nullable=False)
    discord_username = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.String(500), nullable=True)
    access_token = db.Column(db.String(500), nullable=True)
    refresh_token = db.Column(db.String(500), nullable=True)
    permissions = db.Column(db.JSON, default=lambda: ['view_dashboard', 'manage_users'])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AdminUser {self.discord_username}>'

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='activity_logs', lazy=True)
    
    def __repr__(self):
        return f'<ActivityLog {self.action}>'

class Wishlist(db.Model):
    __tablename__ = 'wishlists'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    item_category = db.Column(db.String(100), nullable=False)
    max_price = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='active', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Wishlist {self.item_name}>'

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transaction = db.relationship('Transaction', backref='reviews', lazy=True)
    
    def __repr__(self):
        return f'<Review {self.rating} stars>'

class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    
    id = db.Column(db.Integer, primary_key=True)
    item_name = db.Column(db.String(200), nullable=False)
    item_category = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    condition = db.Column(db.String(50), nullable=True)
    sold_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PriceHistory {self.item_name}: {self.price}>'

class ServerSettings(db.Model):
    __tablename__ = 'server_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.String(20), unique=True, nullable=False)
    marketplace_enabled = db.Column(db.Boolean, default=True)
    verification_required = db.Column(db.Boolean, default=True)
    min_rep_to_trade = db.Column(db.Float, default=0.0)
    max_listings_per_user = db.Column(db.Integer, default=10)
    listing_duration_days = db.Column(db.Integer, default=30)
    welcome_message = db.Column(db.Text, nullable=True)
    rules_channel = db.Column(db.String(20), nullable=True)
    marketplace_channel = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ServerSettings {self.guild_id}>'

class MarketAnalytics(db.Model):
    __tablename__ = 'market_analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_listings = db.Column(db.Integer, default=0)
    total_transactions = db.Column(db.Integer, default=0)
    total_value = db.Column(db.Integer, default=0)
    popular_categories = db.Column(db.JSON, nullable=True)
    average_prices = db.Column(db.JSON, nullable=True)
    
    def __repr__(self):
        return f'<MarketAnalytics {self.date}>'
from datetime import datetime
from enum import Enum

class UserStatus(Enum):
    PENDING = 'pending'
    VERIFIED = 'verified'
    BANNED = 'banned'

class ListingStatus(Enum):
    ACTIVE = 'active'
    SOLD = 'sold'
    EXPIRED = 'expired'
    REMOVED = 'removed'

# Placeholder models for web app compatibility
class User:
    def __init__(self, discord_id, discord_username, highrise_username=None):
        self.discord_id = discord_id
        self.discord_username = discord_username
        self.highrise_username = highrise_username
        self.status = UserStatus.PENDING
        self.created_at = datetime.utcnow()
        self.verified_at = None

class AdminUser:
    def __init__(self, discord_id, discord_username):
        self.discord_id = discord_id
        self.discord_username = discord_username
        self.created_at = datetime.utcnow()
        self.last_login = datetime.utcnow()

class Listing:
    def __init__(self, seller_id, item_name, item_category, price):
        self.seller_id = seller_id
        self.item_name = item_name
        self.item_category = item_category
        self.price = price
        self.status = ListingStatus.ACTIVE
        self.created_at = datetime.utcnow()

class Transaction:
    def __init__(self, listing_id, buyer_id, seller_id, amount):
        self.listing_id = listing_id
        self.buyer_id = buyer_id
        self.seller_id = seller_id
        self.amount = amount
        self.created_at = datetime.utcnow()

class ActivityLog:
    def __init__(self, user_id, action, details=None, ip_address=None, user_agent=None):
        self.user_id = user_id
        self.action = action
        self.details = details
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.created_at = datetime.utcnow()
