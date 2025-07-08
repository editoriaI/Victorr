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
    status = db.Column(db.Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    listings = db.relationship('Listing', backref='seller', lazy=True, cascade='all, delete-orphan')
    transactions_as_buyer = db.relationship('Transaction', foreign_keys='Transaction.buyer_id', backref='buyer', lazy=True)
    transactions_as_seller = db.relationship('Transaction', foreign_keys='Transaction.seller_id', backref='seller', lazy=True)
    
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
    status = db.Column(db.Enum(ListingStatus), default=ListingStatus.ACTIVE, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    
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
