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
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.trade_service import TradeService
import atexit

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
            
            # Ensure users table has all required columns
            try:
                # Check if updated_at exists
                result = db.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND column_name = 'updated_at'
                """)).scalar()
                
                if result == 0:
                    db.session.execute(text("""
                        ALTER TABLE users 
                        ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    """))
                    db.session.commit()
                    app.logger.info("Added updated_at column to users table")
            except Exception as e:
                app.logger.error(f"Error checking/adding updated_at to users: {e}")
                db.session.rollback()
            
            # Ensure trade_recommendations table has all required columns
            try:
                # Check if table exists
                result = db.session.execute(text("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_name = 'trade_recommendations'
                """)).scalar()
                
                if result == 0:
                    # Create table with all required columns
                    db.session.execute(text("""
                        CREATE TABLE trade_recommendations (
                            id BIGINT PRIMARY KEY AUTO_INCREMENT,
                            symbol VARCHAR(10) NOT NULL,
                            action VARCHAR(4) NOT NULL,
                            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                            amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
                            shares DECIMAL(10,4) NOT NULL DEFAULT 0.0000,
                            timeframe VARCHAR(20) NOT NULL DEFAULT '1D',
                            expires_at DATETIME NOT NULL,
                            required_acceptances INT NOT NULL DEFAULT 1,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        )
                    """))
                    db.session.commit()
                    app.logger.info("Created trade_recommendations table")
                else:
                    # Check and add missing columns
                    columns = ['status', 'amount', 'shares', 'timeframe', 'expires_at', 'required_acceptances', 'updated_at']
                    for column in columns:
                        result = db.session.execute(text(f"""
                            SELECT COUNT(*) 
                            FROM information_schema.columns 
                            WHERE table_name = 'trade_recommendations' 
                            AND column_name = '{column}'
                        """)).scalar()
                        
                        if result == 0:
                            if column == 'status':
                                db.session.execute(text("""
                                    ALTER TABLE trade_recommendations 
                                    ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                                """))
                            elif column == 'amount':
                                db.session.execute(text("""
                                    ALTER TABLE trade_recommendations 
                                    ADD COLUMN amount DECIMAL(10,2) NOT NULL DEFAULT 0.00
                                """))
                            elif column == 'shares':
                                db.session.execute(text("""
                                    ALTER TABLE trade_recommendations 
                                    ADD COLUMN shares DECIMAL(10,4) NOT NULL DEFAULT 0.0000
                                """))
                            elif column == 'timeframe':
                                db.session.execute(text("""
                                    ALTER TABLE trade_recommendations 
                                    ADD COLUMN timeframe VARCHAR(20) NOT NULL DEFAULT '1D'
                                """))
                            elif column == 'expires_at':
                                db.session.execute(text("""
                                    ALTER TABLE trade_recommendations 
                                    ADD COLUMN expires_at DATETIME NOT NULL
                                """))
                            elif column == 'required_acceptances':
                                db.session.execute(text("""
                                    ALTER TABLE trade_recommendations 
                                    ADD COLUMN required_acceptances INT NOT NULL DEFAULT 1
                                """))
                            elif column == 'updated_at':
                                db.session.execute(text("""
                                    ALTER TABLE trade_recommendations 
                                    ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                                """))
                            db.session.commit()
                            app.logger.info(f"Added {column} column to trade_recommendations table")
                
            except Exception as e:
                app.logger.error(f"Error verifying table columns: {e}")
                db.session.rollback()
            
        trade_service = TradeService()
        scheduler = BackgroundScheduler()
        def run_expiry_and_execution():
            with app.app_context():
                result = trade_service.process_expiry_and_execution()
                app.logger.info(f"Processed expiry and execution: {result}")
        scheduler.add_job(run_expiry_and_execution, 'interval', minutes=1)
        scheduler.start()
        atexit.register(lambda: scheduler.shutdown())
        
    except Exception as e:
        app.logger.error(f"Error initializing database: {e}")
        
    # Register blueprints/routes
    from app.routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    
    return app 