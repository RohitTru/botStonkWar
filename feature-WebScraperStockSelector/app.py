import os
import logging
from app import create_app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Get environment from environment variable or default to development
env = os.getenv('FLASK_ENV', 'development')
logger.debug(f"Starting application in {env} mode")

try:
    # Create Flask app with appropriate config
    logger.debug("Creating Flask application...")
    app = create_app(env)
    
    if __name__ == '__main__':
        logger.debug("Starting Flask server...")
        app.run(
            host='0.0.0.0',
            port=int(os.getenv('APP_PORT', 5004)),
            debug=False  # Disable debug mode to avoid watchdog issues
        )
except Exception as e:
    logger.error(f"Failed to start application: {str(e)}", exc_info=True)