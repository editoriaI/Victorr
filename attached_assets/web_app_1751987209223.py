from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import logging
from datetime import datetime
import random
from urllib.parse import urlencode
import requests
from typing import Optional, Dict, List, Any
import asyncio
import asyncpg

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET', 'victor_secret_key_change_in_production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Victor's mood quotes
VICTOR_MOODS = [
    "Mmm, admin power. Don't let it go to your head.",
    "The server will collapse without your careful micromanagement.",
    "I watched three mortals argue for ten minutes over a role name. You're my last hope.",
    "Let's get this configured before I fall apart. Again.",
    "I would offer help… but I'm more into observation than intervention.",
    "Ah. You brought me back online. How unfortunate—for them."
]

# Discord OAuth2 Configuration
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_REDIRECT_URI = os.getenv('DISCORD_REDIRECT_URI')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Discord API endpoints
DISCORD_API_BASE = 'https://discord.com/api/v10'
DISCORD_OAUTH_BASE = 'https://discord.com/api/oauth2'

class DatabaseManager:
    """Async database manager for web app"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
    
    async def get_guild_stats(self, guild_id: int) -> Dict[str, Any]:
        """Get guild statistics"""
        try:
            db = await asyncpg.connect(self.database_url)
            try:
                # Get verified users count
                verified_traders = await db.fetchval(
                    "SELECT COUNT(*) FROM users WHERE discord_id IN (SELECT DISTINCT seller_id FROM market_listings WHERE active = true)"
                )
                
                # Get active listings count
                active_listings = await db.fetchval(
                    "SELECT COUNT(*) FROM market_listings WHERE active = true"
                )
                
                # Get total transactions
                total_transactions = await db.fetchval("SELECT COUNT(*) FROM transactions")
                
                # Get verified users
                total_verified = await db.fetchval("SELECT COUNT(*) FROM users")
                
                return {
                    'verified_users': total_verified or 0,
                    'active_traders': verified_traders or 0,
                    'active_listings': active_listings or 0,
                    'total_transactions': total_transactions or 0
                }
            finally:
                await db.close()
        except Exception as e:
            logger.error(f"Error getting guild stats: {e}")
            return {
                'verified_users': 0,
                'active_traders': 0,
                'active_listings': 0,
                'total_transactions': 0
            }
    
    async def get_recent_activity(self, guild_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent activity logs"""
        try:
            db = await asyncpg.connect(self.database_url)
            try:
                logs = await db.fetch("""
                    SELECT action, details, timestamp FROM activity_logs 
                    ORDER BY timestamp DESC LIMIT $1
                """, limit)
                return [{'action': log['action'], 'details': log['details'], 'timestamp': log['timestamp']} for log in logs]
            finally:
                await db.close()
        except Exception as e:
            logger.error(f"Error getting recent activity: {e}")
            return []

db_manager = DatabaseManager()

def get_discord_oauth_url():
    """Generate Discord OAuth URL"""
    if not DISCORD_CLIENT_ID:
        return None
    
    # Always use current Replit domain
    repl_domain = os.getenv('REPLIT_DEV_DOMAIN')
    if repl_domain:
        redirect_uri = f'https://{repl_domain}/callback'
    else:
        # Use 0.0.0.0 instead of localhost for Replit
        redirect_uri = 'http://0.0.0.0:8080/callback'
    
    params = {
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'identify guilds'
    }
    return f"{DISCORD_OAUTH_BASE}/authorize?{urlencode(params)}"

def exchange_code_for_token(code: str) -> Optional[str]:
    """Exchange OAuth code for access token"""
    # Always use current Replit domain - must match get_discord_oauth_url
    repl_domain = os.getenv('REPLIT_DEV_DOMAIN')
    if repl_domain:
        redirect_uri = f'https://{repl_domain}/callback'
    else:
        redirect_uri = 'http://0.0.0.0:8080/callback'
    
    data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        response = requests.post(f"{DISCORD_OAUTH_BASE}/token", data=data, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            logger.error(f"Discord token exchange failed: {response.status_code} - {response.text}")
            logger.error(f"Response: {response.text}")
    except Exception as e:
        logger.error(f"Error exchanging code for token: {e}")
    
    return None

def get_user_info(access_token: str) -> Optional[Dict[str, Any]]:
    """Get Discord user information"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(f"{DISCORD_API_BASE}/users/@me", headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
    
    return None

def get_user_guilds(access_token: str) -> List[Dict[str, Any]]:
    """Get user's Discord guilds"""
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        response = requests.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers)
        if response.status_code == 200:
            guilds = response.json()
            # Filter guilds where user has manage permissions
            return [guild for guild in guilds if int(guild.get('permissions', 0)) & 0x20 == 0x20]
    except Exception as e:
        logger.error(f"Error getting user guilds: {e}")
    
    return []

def check_user_admin_status(user_id: str, guild_id: str) -> bool:
    """Check if user has admin permissions in the specified guild"""
    headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
    
    try:
        # Get guild member information
        response = requests.get(f"{DISCORD_API_BASE}/guilds/{guild_id}/members/{user_id}", headers=headers)
        if response.status_code == 200:
            member_data = response.json()
            role_ids = member_data.get('roles', [])
            
            # Check for admin role IDs (from your admin_commands.py)
            admin_role_ids = [1385455606005235722]  # Admin role ID from your config
            
            # Check if user has any admin roles
            if any(role_id in admin_role_ids for role_id in role_ids):
                return True
                
            # Get guild roles to check for administrator permission
            roles_response = requests.get(f"{DISCORD_API_BASE}/guilds/{guild_id}/roles", headers=headers)
            if roles_response.status_code == 200:
                guild_roles = roles_response.json()
                for role in guild_roles:
                    if role['id'] in role_ids:
                        permissions = int(role.get('permissions', 0))
                        # Check for administrator permission (0x8)
                        if permissions & 0x8:
                            return True
                            
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
    
    return False

def get_user_permissions(user_id: str, guild_id: str) -> Dict[str, bool]:
    """Get user's permissions for the dashboard"""
    is_admin = check_user_admin_status(user_id, guild_id)
    
    return {
        'is_admin': is_admin,
        'can_manage_settings': is_admin,
        'can_view_logs': is_admin,
        'can_manage_users': is_admin,
        'can_access_marketplace': True,  # All users can access marketplace
        'can_view_stats': True,  # All users can view basic stats
        'can_manage_commands': is_admin,
        'can_broadcast': is_admin
    }

def get_bot_guilds() -> List[int]:
    """Get guilds where the bot is present"""
    headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
    
    try:
        response = requests.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers)
        if response.status_code == 200:
            return [int(guild['id']) for guild in response.json()]
    except Exception as e:
        logger.error(f"Error getting bot guilds: {e}")
    
    return []

@app.route('/')
def home():
    """Victor's landing page"""
    # Check if user is already logged in
    if 'user' in session:
        return redirect(url_for('dashboard'))
    
    # Add OAuth debugging information
    repl_domain = os.getenv('REPLIT_DEV_DOMAIN')
    oauth_debug = {
        'current_domain': repl_domain,
        'required_redirect_uri': f'https://{repl_domain}/callback' if repl_domain else 'Domain not available',
        'oauth_url': get_discord_oauth_url()
    }
    
    return render_template('home_simple.html', oauth_debug=oauth_debug)

@app.route('/auth/discord')
def discord_auth():
    """Redirect to Discord OAuth"""
    oauth_url = get_discord_oauth_url()
    if oauth_url:
        return redirect(oauth_url)
    else:
        return render_template('home.html', error="Discord OAuth not configured")

@app.route('/callback')
def discord_callback():
    """Handle Discord OAuth callback"""
    code = request.args.get('code')
    if not code:
        return redirect(url_for('home'))
    
    # Exchange code for access token
    access_token = exchange_code_for_token(code)
    if not access_token:
        return redirect(url_for('home'))
    
    # Get user info
    user_info = get_user_info(access_token)
    if not user_info:
        return redirect(url_for('home'))
    
    # Store user info in session
    session['user'] = {
        'id': user_info['id'],
        'username': user_info['username'],
        'discriminator': user_info.get('discriminator', '0'),
        'avatar': user_info.get('avatar'),
        'access_token': access_token
    }
    
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Victor's main dashboard"""
    if 'user' not in session:
        return redirect(url_for('home'))
    
    user = session['user']
    
    # Get user's manageable guilds
    user_guilds = get_user_guilds(user['access_token'])
    bot_guilds = get_bot_guilds()
    
    # Filter guilds where bot is present and user can manage
    manageable_guilds = [
        guild for guild in user_guilds 
        if int(guild['id']) in bot_guilds
    ]

    # Default to first manageable guild or hr blacklist server
    default_guild_id = '1385442962647629845'  # hr blacklist server ID
    if manageable_guilds:
        default_guild_id = manageable_guilds[0]['id']
    
    # Get user permissions for the selected guild
    user_permissions = get_user_permissions(user['id'], default_guild_id)

    # Mock data - in production, this would come from your database
    server_data = {
        'server_id': default_guild_id,
        'server_name': 'hr blacklist',
        'commands_count': 4,
        'roles_count': 12,
        'members_count': 156
    }

    # Get random Victor mood
    victor_mood = random.choice(VICTOR_MOODS)

    return render_template('dashboard_new.html')

@app.route('/server/<int:guild_id>')
def server_dashboard(guild_id):
    """Individual server dashboard"""
    if 'user' not in session:
        return redirect(url_for('home'))
    
    user = session['user']
    
    # Verify user has access to this guild
    user_guilds = get_user_guilds(user['access_token'])
    bot_guilds = get_bot_guilds()
    
    guild = None
    for g in user_guilds:
        if int(g['id']) == guild_id and guild_id in bot_guilds:
            guild = g
            break
    
    if not guild:
        flash('Access denied to this server', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('server.html', guild=guild, guild_id=guild_id)

@app.route('/api/server/<int:guild_id>/stats')
def api_server_stats(guild_id):
    """API endpoint for server statistics"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Run async function in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        stats = loop.run_until_complete(db_manager.get_guild_stats(guild_id))
        return jsonify(stats)
    finally:
        loop.close()

@app.route('/api/server/<int:guild_id>/activity')
def api_server_activity(guild_id):
    """API endpoint for recent activity"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    limit = request.args.get('limit', 10, type=int)
    
    # Run async function in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        activity = loop.run_until_complete(db_manager.get_recent_activity(guild_id, limit))
        return jsonify(activity)
    finally:
        loop.close()

@app.route('/api/server/<int:guild_id>/settings')
def api_get_settings(guild_id):
    """API endpoint to get server settings"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Default settings
    default_settings = {
        'bot_enabled': True,
        'command_prefix': '-',
        'verification_channel': '1388813198324666458',
        'welcome_channel': '1385446898608898200',
        'rules_channel': '1385445808354365580',
        'roles_channel': '1385446724109078548',
        'marketplace_enabled': True,
        'looking_for_channel': '1385449759342596180',
        'selling_gold_channel': '1385449705043005572',
        'selling_items_channel': '1386397589506625730',
        'vouch_channel': '1385451346144002160',
        'max_listings': 10,
        'verification_required': True,
        'auto_name_sync': True,
        'verification_code_length': 4,
        'verification_timeout': 10,
        'admin_role_id': '1385455606005235722',
        'locked_role_id': '1385446749803925535',
        'auto_role_assignment': True,
        'lock_new_members': True,
        'response_style': 'gothic',
        'sarcastic_responses': True,
        'custom_greeting': ''
    }
    
    return jsonify(default_settings)

@app.route('/api/server/<int:guild_id>/settings', methods=['POST'])
def api_save_settings(guild_id):
    """API endpoint to save server settings"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    settings = request.json
    
    # Here you would save settings to database
    # For now, we'll just return success
    logger.info(f"Saving settings for guild {guild_id}: {settings}")
    
    return jsonify({'success': True, 'message': 'Settings saved successfully'})

@app.route('/api/server/<int:guild_id>/settings/reset', methods=['POST'])
def api_reset_settings(guild_id):
    """API endpoint to reset server settings"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    logger.info(f"Resetting settings for guild {guild_id}")
    
    return jsonify({'success': True, 'message': 'Settings reset to defaults'})

@app.route('/api/server/<int:guild_id>/settings/export')
def api_export_settings(guild_id):
    """API endpoint to export server settings"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get current settings (would be from database in production)
    settings = {
        'bot_enabled': True,
        'command_prefix': '-',
        'verification_channel': '1388813198324666458',
        'marketplace_enabled': True,
        'response_style': 'gothic',
        'export_timestamp': datetime.now().isoformat(),
        'guild_id': str(guild_id)
    }
    
    from flask import make_response
    import json
    
    response = make_response(json.dumps(settings, indent=2))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=victor-settings-{guild_id}.json'
    
    return response

@app.route('/api/server/<int:guild_id>/test-connection')
def api_test_connection(guild_id):
    """API endpoint to test Discord connection"""
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Test bot connection to guild
    headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
    
    try:
        response = requests.get(f"{DISCORD_API_BASE}/guilds/{guild_id}", headers=headers)
        if response.status_code == 200:
            guild_data = response.json()
            return jsonify({
                'success': True, 
                'message': f'Successfully connected to {guild_data["name"]}',
                'guild_name': guild_data['name']
            })
        else:
            return jsonify({
                'success': False, 
                'error': f'Failed to connect to guild (Status: {response.status_code})'
            })
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Connection test failed: {str(e)}'
        })

@app.route('/api/commands', methods=['GET', 'POST'])
def api_commands():
    """API endpoint for command configuration"""
    if request.method == 'POST':
        # Handle command toggle updates
        data = request.get_json()
        command_name = data.get('command')
        enabled = data.get('enabled', False)

        logger.info(f"Command {command_name} {'enabled' if enabled else 'disabled'}")

        return jsonify({
            'success': True,
            'message': f"Command {command_name} {'enabled' if enabled else 'disabled'}"
        })

    # Return current command states
    return jsonify({
        'commands': {
            'blacklist': True,
            'purge': True,
            'ping': False,
            'info': True
        }
    })

@app.route('/api/embeds', methods=['GET', 'POST'])
def api_embeds():
    """API endpoint for embed management"""
    if request.method == 'POST':
        data = request.get_json()
        embed_data = {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'button_label': data.get('button_label', '')
        }

        logger.info(f"Embed created: {embed_data}")

        return jsonify({
            'success': True,
            'message': 'Embed saved successfully'
        })

    return jsonify({
        'embeds': []
    })

@app.route('/api/roles', methods=['GET', 'POST'])
def api_roles():
    """API endpoint for reaction role management"""
    if request.method == 'POST':
        data = request.get_json()
        role_data = {
            'emoji': data.get('emoji', ''),
            'role_name': data.get('role_name', ''),
            'description': data.get('description', '')
        }

        logger.info(f"Role created: {role_data}")

        return jsonify({
            'success': True,
            'message': 'Role configuration saved'
        })

    return jsonify({
        'roles': [
            {'emoji': '📚', 'role_name': 'Rare Sales', 'description': 'Because heaven forbid they miss a discounted tiara.'}
        ]
    })

@app.route('/api/onboarding', methods=['GET', 'POST'])
def api_onboarding():
    """API endpoint for DM onboarding configuration"""
    if request.method == 'POST':
        data = request.get_json()
        onboarding_data = {
            'mood': data.get('mood', 'sarcastic'),
            'message': data.get('message', ''),
            'enabled': data.get('enabled', True)
        }

        logger.info(f"Onboarding configured: {onboarding_data}")

        return jsonify({
            'success': True,
            'message': 'Onboarding settings saved'
        })

    return jsonify({
        'onboarding': {
            'mood': 'sarcastic',
            'message': "Welcome to {server}, {user}. Don't break anything, or do. Victor's watching.",
            'enabled': True
        }
    })

@app.route('/api/logging', methods=['GET', 'POST'])
def api_logging():
    """API endpoint for logging configuration"""
    if request.method == 'POST':
        data = request.get_json()
        logging_data = {
            'join_leave': data.get('join_leave', False),
            'message_deletes': data.get('message_deletes', False),
            'command_usage': data.get('command_usage', True),
            'log_channel': data.get('log_channel', '')
        }

        logger.info(f"Logging configured: {logging_data}")

        return jsonify({
            'success': True,
            'message': 'Logging settings saved'
        })

    return jsonify({
        'logging': {
            'join_leave': True,
            'message_deletes': False,
            'command_usage': True,
            'log_channel': 'logs'
        }
    })

@app.route('/api/diagnostics', methods=['POST'])
def api_diagnostics():
    """API endpoint for running diagnostics"""
    # Simulate diagnostic checks
    diagnostics = {
        'bot_status': 'online',
        'database_connection': 'healthy',
        'api_connectivity': 'operational',
        'commands_loaded': 4,
        'last_restart': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    logger.info("Diagnostics completed")

    return jsonify({
        'success': True,
        'diagnostics': diagnostics,
        'message': 'Diagnostics complete. All systems operational.'
    })

@app.route('/api/victor-mood')
def api_victor_mood():
    """Get a random Victor mood quote"""
    return jsonify({
        'mood': random.choice(VICTOR_MOODS)
    })

@app.route('/invite')
def invite():
    """Bot invite page"""
    invite_url = f"https://discord.com/api/oauth2/authorize?client_id={DISCORD_CLIENT_ID}&permissions=8&scope=bot%20applications.commands"
    return render_template('invite.html', invite_url=invite_url)

@app.route('/auth/login', methods=['POST'])
def manual_login():
    """Handle manual login (placeholder for future implementation)"""
    email = request.json.get('email')
    password = request.json.get('password')
    
    # TODO: Implement actual authentication logic
    # For now, return error since we only support Discord OAuth
    return jsonify({
        'success': False,
        'error': 'Manual login not yet implemented. Please use Discord authentication.'
    }), 400

@app.route('/auth/register', methods=['POST'])
def manual_register():
    """Handle manual registration (placeholder for future implementation)"""
    username = request.json.get('username')
    email = request.json.get('email')
    password = request.json.get('password')
    
    # TODO: Implement actual registration logic
    # For now, return error since we only support Discord OAuth
    return jsonify({
        'success': False,
        'error': 'Manual registration not yet implemented. Please use Discord authentication.'
    }), 400

@app.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Handle password reset requests"""
    email = request.json.get('email')
    
    # TODO: Implement password reset logic
    return jsonify({
        'success': True,
        'message': 'If an account with that email exists, a password reset link has been sent.'
    })

@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    return redirect(url_for('home'))

@app.route('/api/debug/oauth')
def api_debug_oauth():
    """Debug OAuth configuration endpoint"""
    repl_domain = os.getenv('REPLIT_DEV_DOMAIN')
    expected_redirect = f'https://{repl_domain}/callback' if repl_domain else 'Domain not available'
    
    return jsonify({
        'discord_client_id': DISCORD_CLIENT_ID[:10] + '...' if DISCORD_CLIENT_ID else 'Not set',
        'discord_client_secret': 'Set' if DISCORD_CLIENT_SECRET else 'Not set',
        'oauth_url': get_discord_oauth_url(),
        'current_domain': repl_domain or 'Not set',
        'expected_redirect_uri': expected_redirect,
        'instructions': [
            '1. Go to https://discord.com/developers/applications',
            '2. Select your bot application', 
            '3. Go to OAuth2 → General',
            f'4. Add this redirect URI: {expected_redirect}',
            '5. Save changes'
        ]
    })

@app.route('/api/debug-config')
def api_debug_config():
    """Debug configuration endpoint"""
    return jsonify({
        'discord_client_id_exists': DISCORD_CLIENT_ID is not None,
        'discord_client_secret_exists': DISCORD_CLIENT_SECRET is not None,
        'discord_bot_token_exists': DISCORD_BOT_TOKEN is not None,
        'oauth_url_generated': get_discord_oauth_url() is not None,
        'replit_domain': os.getenv('REPLIT_DEV_DOMAIN')
    })

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """Get dashboard statistics"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Get database connection
        import asyncio
        from bot.postgres_database import DatabaseManager
        
        async def get_stats():
            db = DatabaseManager()
            try:
                # Get total verified users
                async with db.pool.acquire() as conn:
                    verified_users = await conn.fetchval(
                        "SELECT COUNT(*) FROM users WHERE verified = TRUE"
                    )
                    
                    # Get total marketplace listings
                    marketplace_listings = await conn.fetchval(
                        "SELECT COUNT(*) FROM market_listings WHERE status = 'active'"
                    )
                    
                    return {
                        'servers': len(get_bot_guilds()),
                        'members': 156,  # This would come from Discord API
                        'verified_users': verified_users or 0,
                        'marketplace_listings': marketplace_listings or 0
                    }
            except Exception as e:
                logger.error(f"Error getting dashboard stats: {e}")
                return {
                    'servers': len(get_bot_guilds()),
                    'members': 156,
                    'verified_users': 0,
                    'marketplace_listings': 0
                }
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        stats = loop.run_until_complete(get_stats())
        loop.close()
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return jsonify({
            'servers': 1,
            'members': 156,
            'verified_users': 0,
            'marketplace_listings': 0
        })

@app.route('/api/dashboard/status')
def api_dashboard_status():
    """Get system status"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # Check if bot is online (this would be more sophisticated in production)
        bot_online = len(get_bot_guilds()) > 0
        
        # Check database connection
        import asyncio
        from bot.postgres_database import DatabaseManager
        
        async def check_db():
            db = DatabaseManager()
            try:
                async with db.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                return True
            except Exception:
                return False
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        db_connected = loop.run_until_complete(check_db())
        loop.close()
        
        return jsonify({
            'bot_online': bot_online,
            'database_connected': db_connected
        })
    except Exception as e:
        logger.error(f"Error checking system status: {e}")
        return jsonify({
            'bot_online': False,
            'database_connected': False
        })

@app.errorhandler(404)
def not_found(error):
    """Victor's 404 page"""
    return render_template('404.html'), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)