"""
App initialization for StockBot Brokerage Handler.
"""
from flask import Flask
from dotenv import load_dotenv
import os
from app.database import db
from flask_migrate import Migrate

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    # Initialize Flask-Migrate
    Migrate(app, db)
    # Register blueprints/routes
    from app.routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    from app.routes.dashboard import dashboard_bp
    app.register_blueprint(dashboard_bp)
    return app 