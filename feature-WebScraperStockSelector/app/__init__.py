from flask import Flask
import os
import logging
from dotenv import load_dotenv
from config import config

# Configure logging
logger = logging.getLogger(__name__)

def init_scraper_manager(app):
    """Initialize scraper manager after app is set up."""
    try:
        logger.debug("Initializing scraper manager...")
        from app.scrapers.scraper_manager import ScraperManager
        scraper_manager = ScraperManager()
        scraper_manager.init_app(app)
        logger.debug("Scraper manager initialized successfully")
        return scraper_manager
    except Exception as e:
        logger.error(f"Failed to initialize scraper manager: {str(e)}", exc_info=True)
        # Don't raise the error, just return None
        return None

def create_app(config_name='default'):
    logger.debug(f"Creating Flask app with config: {config_name}")
    
    # Initialize Flask app
    app = Flask(__name__)
    
    # Load environment variables
    logger.debug("Loading environment variables...")
    load_dotenv()
    
    # Load config
    logger.debug("Loading configuration...")
    app.config.from_object(config[config_name])
    
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Import and register blueprints
    logger.debug("Registering blueprints...")
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    # Initialize scraper manager
    if not app.config['TESTING']:  # Don't start scrapers in testing mode
        with app.app_context():
            logger.debug("Starting scraper manager...")
            scraper_manager = init_scraper_manager(app)
            if scraper_manager:  # Only start if initialization was successful
                app.scraper_manager = scraper_manager  # Store reference in app
                scraper_manager.start()
                logger.debug("Scraper manager started successfully")
            else:
                logger.warning("Scraper manager initialization failed, continuing without scraper")
    
    logger.debug("Application creation completed successfully")
    return app 