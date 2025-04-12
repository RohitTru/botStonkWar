from flask import Blueprint, request, jsonify
from datetime import timedelta
from jose import jwt
from app import db, bcrypt
from app.models.models import User
import os

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"

@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    
    # Check if user already exists
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Username already exists"}), 400
        
    # Create new user
    hashed_password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")
    new_user = User(
        username=data["username"],
        email=data["email"],
        hashed_password=hashed_password
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User created successfully"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    
    if user and bcrypt.check_password_hash(user.hashed_password, data["password"]):
        token = jwt.encode(
            {"sub": user.username, "exp": timedelta(minutes=30)},
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        return jsonify({
            "access_token": token,
            "token_type": "bearer"
        })
    
    return jsonify({"error": "Invalid username or password"}), 401 