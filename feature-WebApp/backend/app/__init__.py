from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
bcrypt = Bcrypt()

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@"
        f"{os.getenv('MYSQL_HOST', 'localhost')}/{os.getenv('MYSQL_DATABASE')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.health import health_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(health_bp, url_prefix='/api/health')

    return app 