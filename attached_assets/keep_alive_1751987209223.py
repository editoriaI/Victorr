"""
Keep-alive system integrated with Flask web dashboard
Maintains 24/7 uptime while serving the web interface
"""

from web_app import app
import threading
import logging
import os

logger = logging.getLogger(__name__)

def run():
    """Run the Flask web dashboard"""
    try:
        port = int(os.environ.get('PORT', 8080))
        logger.info(f"Starting Victor's web dashboard on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        logger.error(f"Error starting Flask app: {e}")

def keep_alive():
    """Start the web dashboard in a daemon thread"""
    t = threading.Thread(target=run, name="VictorWebDashboard", daemon=True)
    t.start()
    logger.info("Victor's web dashboard thread started")