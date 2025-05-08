"""
App initialization for StockBot Brokerage Handler.
"""
from flask import Flask
from dotenv import load_dotenv
import os
from app.database import db
from flask_migrate import Migrate
import logging
from sqlalchemy import text

def create_app():
    # Load environment variables
    load_dotenv()
    
    # Initialize Flask app
    app = Flask(__name__)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Database configuration
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    try:
        # Initialize database
        db.init_app(app)
        
        # Initialize Flask-Migrate
        Migrate(app, db)
        
        with app.app_context():
            # Create tables if they don't exist
            db.create_all()
            
            # Ensure trade_recommendations table has all required columns
            try:
                db.session.execute(text("""
                    ALTER TABLE trade_recommendations 
                    ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    ADD COLUMN IF NOT EXISTS updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                """))
                db.session.commit()
                app.logger.info("Database tables and columns verified successfully")
            except Exception as e:
                app.logger.error(f"Error verifying table columns: {e}")
                db.session.rollback()
            
    except Exception as e:
        app.logger.error(f"Error initializing database: {e}")
        
    # Register blueprints/routes
    from app.routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    return app 