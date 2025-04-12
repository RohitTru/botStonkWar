from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from . import create_app, db, bcrypt
from .models.models import User

# Create the Flask application
app = create_app()

# Security
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Routes
@app.route("/")
def root():
    return jsonify({"message": "Welcome to StockBotWar's WebApp API!"})

@app.route("/health")
def health_check():
    return jsonify({"status": "healthy"})

@app.route("/api/auth/signup", methods=["POST"])
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

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    
    if user and bcrypt.check_password_hash(user.hashed_password, data["password"]):
        access_token = create_access_token({"sub": user.username})
        return jsonify({
            "access_token": access_token,
            "token_type": "bearer"
        })
    
    return jsonify({"error": "Invalid username or password"}), 401

# Helper functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("APP_PORT", 5000)))