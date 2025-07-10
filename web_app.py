
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

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect('victor_bot.db')

def log_activity(action, details=None, user_id=None):
    """Log user activity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activity_logs (user_id, action, details, ip_address, user_agent, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, action, str(details) if details else None, request.remote_addr, request.headers.get('User-Agent'), datetime.now())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error logging activity: {e}")

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def require_member_auth(f):
    """Decorator to require member authentication"""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('member_login'))
        
        # Check if user is verified
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM users WHERE discord_id = ?", (session.get('discord_id'),))
        user = cursor.fetchone()
        conn.close()
        
        if not user or user[0] != 'verified':
            flash('You must be a verified member to access this area', 'error')
            return redirect(url_for('member_login'))
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html', discord_client_id=DISCORD_CLIENT_ID)

@app.route('/login')
def login():
    """Admin login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html', login_type='admin')

@app.route('/member-login')
def member_login():
    """Member login page"""
    if 'user_id' in session:
        return redirect(url_for('member_portal'))
    return render_template('login.html', login_type='member')

@app.route('/auth/discord')
def discord_auth():
    """Redirect to Discord OAuth for admin"""
    return discord_auth_helper('admin')

@app.route('/auth/discord/member')
def discord_auth_member():
    """Redirect to Discord OAuth for member"""
    return discord_auth_helper('member')

def discord_auth_helper(auth_type):
    """Helper for Discord OAuth"""
    params = {
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': DISCORD_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify email guilds',
        'state': f"{auth_type}:{secrets.token_urlsafe(32)}"
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
    
    # Extract auth type from state
    auth_type = state.split(':')[0] if ':' in state else 'admin'
    
    if not code:
        flash('Authentication failed', 'error')
        return redirect(url_for('member_login' if auth_type == 'member' else 'login'))
    
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
            return redirect(url_for('member_login' if auth_type == 'member' else 'login'))
        
        access_token = token_json['access_token']
        
        # Get user info
        headers = {'Authorization': f'Bearer {access_token}'}
        user_response = requests.get(f'{DISCORD_API_BASE}/users/@me', headers=headers)
        user_data = user_response.json()
        
        if 'id' not in user_data:
            flash('Failed to get user information', 'error')
            return redirect(url_for('member_login' if auth_type == 'member' else 'login'))
        
        discord_id = user_data['id']
        username = f"{user_data['username']}#{user_data.get('discriminator', '0000')}"
        avatar_url = None
        
        if user_data.get('avatar'):
            avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{user_data['avatar']}.png"
        
        # Check if user exists in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
        user = cursor.fetchone()
        
        if auth_type == 'admin':
            # Admin login - check for admin privileges (simplified)
            admin_ids = ['223906501008424961']  # Add your Discord ID here
            if discord_id not in admin_ids:
                flash('Access denied. Admin privileges required.', 'error')
                conn.close()
                return redirect(url_for('login'))
            
            session['user_id'] = discord_id
            session['discord_id'] = discord_id
            session['username'] = username
            session['avatar_url'] = avatar_url
            session['is_admin'] = True
            
            conn.close()
            log_activity('admin_login_success', {'discord_id': discord_id}, discord_id)
            flash('Successfully logged in as admin!', 'success')
            return redirect(url_for('dashboard'))
        
        else:  # member login
            if not user:
                flash('Account not found. Please verify your account first using the Discord bot.', 'error')
                conn.close()
                return redirect(url_for('member_login'))
            
            if user[6] != 'verified':  # status column
                flash('Your account is not verified. Please complete verification using the Discord bot.', 'warning')
                conn.close()
                return redirect(url_for('member_login'))
            
            session['user_id'] = user[0]  # database ID
            session['discord_id'] = discord_id
            session['username'] = username
            session['avatar_url'] = avatar_url
            session['highrise_username'] = user[3]  # highrise_username column
            session['is_admin'] = False
            
            conn.close()
            log_activity('member_login_success', {'discord_id': discord_id}, user[0])
            flash('Welcome back to the marketplace!', 'success')
            return redirect(url_for('member_portal'))
        
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        flash(f'Authentication error: {str(e)}', 'error')
        return redirect(url_for('member_login' if auth_type == 'member' else 'login'))

@app.route('/dashboard')
@require_auth
def dashboard():
    """Admin dashboard"""
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
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 5")
        recent_users = cursor.fetchall()
        
        cursor.execute("SELECT * FROM listings ORDER BY created_at DESC LIMIT 5")
        recent_listings = cursor.fetchall()
        
        conn.close()
        
        stats = {
            'total_users': total_users,
            'verified_users': verified_users,
            'active_listings': active_listings,
            'total_transactions': 0
        }
        
        return render_template('dashboard.html', 
                             stats=stats,
                             recent_users=recent_users,
                             recent_listings=recent_listings)
                             
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', stats={})

@app.route('/member-portal')
@require_member_auth
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
def web_verify():
    """Web-based verification"""
    if request.method == 'POST':
        highrise_username = request.form.get('highrise_username')
        discord_id = session.get('discord_id')
        
        if not discord_id:
            flash('Please log in first', 'error')
            return redirect(url_for('member_login'))
        
        try:
            # Generate verification code
            import random
            import string
            verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Save to database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE discord_id = ?", (discord_id,))
            user = cursor.fetchone()
            
            if user:
                # Update existing user
                cursor.execute(
                    "UPDATE users SET highrise_username = ?, verification_code = ? WHERE discord_id = ?",
                    (highrise_username, verification_code, discord_id)
                )
            else:
                # Create new user
                cursor.execute(
                    "INSERT INTO users (discord_id, discord_username, highrise_username, verification_code, status) VALUES (?, ?, ?, ?, 'pending')",
                    (discord_id, session.get('username'), highrise_username, verification_code)
                )
            
            conn.commit()
            conn.close()
            
            flash(f'Please add this code to your Highrise bio: {verification_code}', 'info')
            return render_template('verify.html', verification_code=verification_code, highrise_username=highrise_username)
            
        except Exception as e:
            logger.error(f"Verification error: {e}")
            flash(f'Verification error: {str(e)}', 'error')
    
    return render_template('verify.html')

@app.route('/marketplace')
@require_member_auth
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
@require_auth
def api_stats():
    """API endpoint for dashboard statistics"""
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
