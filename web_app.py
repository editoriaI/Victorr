
"""
Victor's Web Dashboard
Flask application for Discord bot administration and member portal
"""

import os
import requests
import secrets
from urllib.parse import urlencode
from datetime import datetime
import sqlite3
import logging

from flask import render_template, request, redirect, url_for, session, flash, jsonify
from app import app

logger = logging.getLogger(__name__)

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID', '1370481883326402652')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET', 'QKqzCRl1FQM6lJnwm1jJGMnuJg1tDN1g')
DISCORD_REDIRECT_URI = f'https://{os.getenv("REPLIT_DEV_DOMAIN", "localhost:5000")}/auth/discord/callback'
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')

# Discord API endpoints
DISCORD_API_BASE = 'https://discord.com/api/v10'
DISCORD_OAUTH_URL = 'https://discord.com/api/oauth2/authorize'
DISCORD_TOKEN_URL = 'https://discord.com/api/oauth2/token'

# Admin Discord IDs - Add your Discord ID here
ADMIN_IDS = ['223906501008424961']  # Replace with actual admin Discord IDs

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect('victor_bot.db')

def log_activity(action, details=None, user_id=None):
    """Log user activity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create activity_logs table if it doesn't exist (simplified version)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute(
            "INSERT INTO activity_logs (user_id, action, details, ip_address, user_agent, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, action, str(details) if details else None, request.remote_addr, 
             request.headers.get('User-Agent'), datetime.now())
        )
        conn.commit()
        conn.close()
        
        # Also log to console for real-time monitoring
        logger.info(f"User Activity: {action} | User: {user_id or 'Anonymous'} | IP: {request.remote_addr}")
        
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

def require_auth(f):
    """Decorator to require authentication - now optional"""
    def decorated_function(*args, **kwargs):
        # No authentication required - allow all access
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_verified_user(f):
    """Decorator to require verified user - now optional"""
    def decorated_function(*args, **kwargs):
        # No verification required - allow all access
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.before_request
def log_request():
    """Log all incoming requests"""
    # Skip logging for static files and health checks
    if not request.endpoint or request.endpoint == 'static':
        return
    
    # Log as anonymous user
    log_activity(
        f"page_visit_{request.endpoint}", 
        {
            'method': request.method,
            'args': dict(request.args),
            'form_data': dict(request.form) if request.form else None,
            'username': 'Anonymous'
        }, 
        'anonymous'
    )

@app.route('/')
def index():
    """Landing page - redirect to dashboard"""
    return redirect(url_for('dashboard'))

@app.route('/login')
def login():
    """Unified login page"""
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('dashboard'))
        else:
            return redirect(url_for('member_portal'))
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
        return redirect(url_for('index'))
    
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
        
        # Get user info
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(f'{DISCORD_API_BASE}/users/@me', headers=headers)
        user_data = user_response.json()
        
        if 'id' not in user_data:
            flash('Failed to get user information', 'error')
            return redirect(url_for('login'))
        
        discord_id = user_data['id']
        username = f"{user_data['username']}#{user_data.get('discriminator', '0000')}"
        avatar_url = None
        
        if user_data.get('avatar'):
            avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{user_data['avatar']}.png"
        
        # Check if user is admin
        is_admin = discord_id in ADMIN_IDS
        
        # Check if user exists in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
        user = cursor.fetchone()
        
        if is_admin:
            # Admin access
            session['user_id'] = discord_id
            session['discord_id'] = discord_id
            session['username'] = username
            session['avatar_url'] = avatar_url
            session['is_admin'] = True
            
            conn.close()
            log_activity('admin_login_success', {'discord_id': discord_id}, discord_id)
            flash('Welcome to Victor\'s domain, dark one.', 'success')
            return redirect(url_for('dashboard'))
        
        else:
            # Regular user access
            if not user:
                # Create a pending user record for verification
                cursor.execute(
                    "INSERT INTO users (discord_id, discord_username, status) VALUES (?, ?, 'pending')",
                    (discord_id, username)
                )
                conn.commit()
                user_id = cursor.lastrowid
                
                session['user_id'] = user_id
                session['discord_id'] = discord_id
                session['username'] = username
                session['avatar_url'] = avatar_url
                session['is_admin'] = False
                
                conn.close()
                log_activity('new_user_login', {'discord_id': discord_id, 'username': username}, user_id)
                flash('Welcome! Please complete verification to access the marketplace.', 'info')
                return redirect(url_for('verify'))
            
            session['user_id'] = user[0]  # database ID
            session['discord_id'] = discord_id
            session['username'] = username
            session['avatar_url'] = avatar_url
            session['highrise_username'] = user[3] if user[3] else None  # highrise_username column
            session['is_admin'] = False
            
            conn.close()
            log_activity('member_login_success', {'discord_id': discord_id, 'username': username}, user[0])
            flash('Welcome back to the depths of the marketplace.', 'success')
            return redirect(url_for('member_portal'))
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Admin dashboard - now accessible to all"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'verified'")
        verified_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM listings WHERE status = 'active'")
        active_listings = cursor.fetchone()[0]
        
        # Get recent activity
        cursor.execute("SELECT id, discord_id, discord_username, highrise_username, status, created_at FROM users ORDER BY created_at DESC LIMIT 5")
        recent_users_raw = cursor.fetchall()
        
        cursor.execute("SELECT id, seller_id, item_name, price, status, created_at FROM listings ORDER BY created_at DESC LIMIT 5")
        recent_listings_raw = cursor.fetchall()
        
        # Convert tuples to dictionaries for easier template access
        recent_users = []
        for user in recent_users_raw:
            recent_users.append({
                'id': user[0],
                'discord_id': user[1],
                'discord_username': user[2],
                'highrise_username': user[3],
                'status': user[4],
                'created_at': user[5]
            })
        
        recent_listings = []
        for listing in recent_listings_raw:
            recent_listings.append({
                'id': listing[0],
                'seller_id': listing[1],
                'item_name': listing[2],
                'price': listing[3],
                'status': listing[4],
                'created_at': listing[5]
            })
        
        conn.close()
        
        stats = {
            'total_users': total_users,
            'verified_users': verified_users,
            'active_listings': active_listings,
            'total_transactions': 0
        }
        
        # Create a mock session for template compatibility
        mock_session = {
            'username': 'Victor Admin',
            'is_admin': True,
            'user_id': 'admin'
        }
        
        return render_template('dashboard.html', 
                             stats=stats,
                             recent_users=recent_users,
                             recent_listings=recent_listings,
                             session=mock_session)
                             
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', stats={}, session={'username': 'Victor Admin'})

@app.route('/member-portal')
@require_verified_user
def member_portal():
    """Member portal dashboard"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user's listings
        cursor.execute("SELECT * FROM listings WHERE seller_id = ? ORDER BY created_at DESC", 
                      (session['user_id'],))
        user_listings = cursor.fetchall()
        
        # Get recent marketplace activity
        cursor.execute("SELECT * FROM listings WHERE status = 'active' ORDER BY created_at DESC LIMIT 10")
        recent_listings = cursor.fetchall()
        
        conn.close()
        
        return render_template('member_portal.html', 
                             user_listings=user_listings,
                             recent_listings=recent_listings,
                             highrise_username=session.get('highrise_username'))
                             
    except Exception as e:
        logger.error(f"Error loading member portal: {e}")
        flash(f'Error loading member portal: {str(e)}', 'error')
        return render_template('member_portal.html', user_listings=[], recent_listings=[])

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    """Web-based verification"""
    if request.method == 'POST':
        highrise_username = request.form.get('highrise_username', '').strip()
        discord_id = session.get('discord_id')
        
        if not discord_id:
            flash('Please log in first', 'error')
            return redirect(url_for('login'))
        
        if not highrise_username:
            flash('Please enter a valid Highrise username', 'error')
            return render_template('verify.html')
        
        try:
            # Generate verification code
            import random
            import string
            verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Save to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if user exists (case-insensitive check for existing users)
            cursor.execute("SELECT id, highrise_username FROM users WHERE discord_id = ?", (discord_id,))
            user = cursor.fetchone()
            
            # Also check if this Highrise username is already taken by someone else (case-insensitive)
            cursor.execute("SELECT discord_id FROM users WHERE LOWER(highrise_username) = LOWER(?) AND discord_id != ?", 
                          (highrise_username, discord_id))
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash(f'Highrise username "{highrise_username}" is already linked to another Discord account', 'error')
                conn.close()
                return render_template('verify.html')
            
            if user:
                # Update existing user
                cursor.execute(
                    "UPDATE users SET highrise_username = ?, verification_code = ?, status = 'pending' WHERE discord_id = ?",
                    (highrise_username, verification_code, discord_id)
                )
                logger.info(f"Updated existing user {discord_id} with Highrise username: {highrise_username}")
            else:
                # Create new user
                cursor.execute(
                    "INSERT INTO users (discord_id, discord_username, highrise_username, verification_code, status) VALUES (?, ?, ?, ?, 'pending')",
                    (discord_id, session.get('username'), highrise_username, verification_code)
                )
                logger.info(f"Created new user {discord_id} with Highrise username: {highrise_username}")
            
            conn.commit()
            conn.close()
            
            log_activity('verification_code_generated', {
                'highrise_username': highrise_username,
                'verification_code': verification_code
            }, discord_id)
            
            flash(f'Verification code generated! Please add this code to your Highrise bio: {verification_code}', 'info')
            return render_template('verify.html', verification_code=verification_code, highrise_username=highrise_username)
            
        except Exception as e:
            logger.error(f"Verification error for {discord_id}: {e}")
            flash(f'Verification error: {str(e)}', 'error')
    
    return render_template('verify.html')

@app.route('/marketplace')
@require_verified_user
def marketplace():
    """Member marketplace view"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        
        query = "SELECT l.*, u.discord_username, u.highrise_username FROM listings l JOIN users u ON l.seller_id = u.id WHERE l.status = 'active'"
        params = []
        
        if search:
            query += " AND l.item_name LIKE ?"
            params.append(f"%{search}%")
        
        if category:
            query += " AND l.item_category = ?"
            params.append(category)
        
        query += " ORDER BY l.created_at DESC LIMIT 20"
        
        cursor.execute(query, params)
        listings = cursor.fetchall()
        
        conn.close()
        
        return render_template('marketplace.html', listings=listings, search=search, category=category)
        
    except Exception as e:
        logger.error(f"Error loading marketplace: {e}")
        flash(f'Error loading marketplace: {str(e)}', 'error')
        return render_template('marketplace.html', listings=[])

@app.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics - now public"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'verified'")
        verified_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM listings WHERE status = 'active'")
        active_listings = cursor.fetchone()[0]
        
        conn.close()
        
        stats = {
            'total_users': total_users,
            'verified_users': verified_users,
            'active_listings': active_listings,
            'total_transactions': 0
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
    flash('You have been banished from Victor\'s domain.', 'info')
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
