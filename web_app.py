
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
    """Simple hi page"""
    return render_template('index.html')

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
