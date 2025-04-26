from flask import Flask
from app.routes import main_bp
from app.scrapers.scraper_manager import ScraperManager
from app.database import Database
from config import config
import os
from app.utils.logging import setup_logger

logger = setup_logger()

def create_app(config_name='production'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize database
    db = Database()
    
    # Initialize scraper manager with database instance
    app.scraper_manager = ScraperManager(db)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    
    # Start scraper
    app.scraper_manager.start()
    
    return app

if __name__ == '__main__':
    # Get environment from environment variable
    env = os.getenv('FLASK_ENV', 'production')
    
    # Create and run app
    app = create_app(env)
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('APP_PORT', 5004)),
        debug=False
    )