"""
Victor's Web Dashboard
Flask application for Discord bot administration
"""

import os
import requests
import secrets
from urllib.parse import urlencode
from datetime import datetime

from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app import app, db
from models import User, AdminUser, Listing, Transaction, ActivityLog, UserStatus, ListingStatus

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', '1234567890')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET', 'your_client_secret')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI', 'https://victor-discord-bot.repl.co/auth/discord/callback')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')

# Discord API endpoints
DISCORD_API_BASE = 'https://discord.com/api/v10'
DISCORD_OAUTH_URL = 'https://discord.com/api/oauth2/authorize'
DISCORD_TOKEN_URL = 'https://discord.com/api/oauth2/token'

def log_activity(action, details=None, user_id=None):
    """Log user activity"""
    try:
        activity = ActivityLog(
            user_id=user_id,
            action=action,
            details=details,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        print(f"Error logging activity: {e}")

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/auth/discord')
def discord_auth():
    """Redirect to Discord OAuth"""
    params = {
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': DISCORD_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify email guilds',
        'state': secrets.token_urlsafe(32)
    }
    
    session['oauth_state'] = params['state']
    auth_url = f"{DISCORD_OAUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)

@app.route('/auth/discord/callback')
def discord_callback():
    """Handle Discord OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    
    # Verify state
    if not state or state != session.get('oauth_state'):
        flash('Invalid authentication state', 'error')
        return redirect(url_for('login'))
    
    if not code:
        flash('Authentication failed', 'error')
        return redirect(url_for('login'))
    
    try:
        # Exchange code for token
        token_data = {
            'client_id': DISCORD_CLIENT_ID,
            'client_secret': DISCORD_CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': DISCORD_REDIRECT_URI
        }
        
        token_response = requests.post(DISCORD_TOKEN_URL, data=token_data)
        token_json = token_response.json()
        
        if 'access_token' not in token_json:
            flash('Failed to get access token', 'error')
            return redirect(url_for('login'))
        
        access_token = token_json['access_token']
        refresh_token = token_json.get('refresh_token')
        
        # Get user info
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(f'{DISCORD_API_BASE}/users/@me', headers=headers)
        user_data = user_response.json()
        
        if 'id' not in user_data:
            flash('Failed to get user information', 'error')
            return redirect(url_for('login'))
        
        # Check if user is admin or bot owner
        discord_id = user_data['id']
        username = f"{user_data['username']}#{user_data.get('discriminator', '0000')}"
        avatar_url = None
        
        if user_data.get('avatar'):
            avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{user_data['avatar']}.png"
        
        # Create or update admin user
        admin_user = AdminUser.query.filter_by(discord_id=discord_id).first()
        if not admin_user:
            admin_user = AdminUser(
                discord_id=discord_id,
                discord_username=username,
                avatar_url=avatar_url,
                access_token=access_token,
                refresh_token=refresh_token
            )
            db.session.add(admin_user)
        else:
            admin_user.discord_username = username
            admin_user.avatar_url = avatar_url
            admin_user.access_token = access_token
            admin_user.refresh_token = refresh_token
            admin_user.last_login = datetime.utcnow()
        
        db.session.commit()
        
        # Set session
        session['user_id'] = admin_user.id
        session['discord_id'] = discord_id
        session['username'] = username
        session['avatar_url'] = avatar_url
        
        log_activity('login_success', {'discord_id': discord_id}, admin_user.id)
        flash('Successfully logged in!', 'success')
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/dashboard')
@require_auth
def dashboard():
    """Main dashboard"""
    try:
        # Get statistics
        total_users = User.query.count()
        verified_users = User.query.filter_by(status=UserStatus.VERIFIED).count()
        active_listings = Listing.query.filter_by(status=ListingStatus.ACTIVE).count()
        total_transactions = Transaction.query.count()
        
        # Get recent activity
        recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
        recent_listings = Listing.query.order_by(Listing.created_at.desc()).limit(5).all()
        recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(5).all()
        
        stats = {
            'total_users': total_users,
            'verified_users': verified_users,
            'active_listings': active_listings,
            'total_transactions': total_transactions
        }
        
        return render_template('dashboard.html', 
                             stats=stats,
                             recent_users=recent_users,
                             recent_listings=recent_listings,
                             recent_transactions=recent_transactions)
                             
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', stats={})

@app.route('/users')
@require_auth
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            (User.discord_username.contains(search)) |
            (User.highrise_username.contains(search))
        )
    
    if status_filter:
        query = query.filter(User.status == status_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('users.html', users=users, search=search, status_filter=status_filter)

@app.route('/marketplace')
@require_auth
def marketplace():
    """Marketplace management page"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category_filter = request.args.get('category', '')
    
    query = Listing.query
    
    if search:
        query = query.filter(Listing.item_name.contains(search))
    
    if category_filter:
        query = query.filter(Listing.item_category == category_filter)
    
    listings = query.order_by(Listing.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('marketplace.html', listings=listings, search=search, category_filter=category_filter)

@app.route('/api/stats')
@require_auth
def api_stats():
    """API endpoint for dashboard statistics"""
    try:
        stats = {
            'total_users': User.query.count(),
            'verified_users': User.query.filter_by(status=UserStatus.VERIFIED).count(),
            'active_listings': Listing.query.filter_by(status=ListingStatus.ACTIVE).count(),
            'total_transactions': Transaction.query.count()
        }
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    """Logout user"""
    user_id = session.get('user_id')
    if user_id:
        log_activity('logout', user_id=user_id)
    
    session.clear()
    flash('Successfully logged out', 'info')
    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
