from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(80), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    hashed_password = db.Column(db.String(128))
    full_name = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    balance = db.Column(db.Float, default=10000.0)
    
    trades = db.relationship("Trade", back_populates="user")
    votes = db.relationship("Vote", back_populates="user")

class Trade(db.Model):
    __tablename__ = "trades"

    id = db.Column(db.Integer, primary_key=True, index=True)
    stock_symbol = db.Column(db.String(10), index=True)
    entry_price = db.Column(db.Float)
    exit_price = db.Column(db.Float, nullable=True)
    quantity = db.Column(db.Integer)
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime, nullable=True)
    trade_type = db.Column(db.String(10))  # 'long' or 'short'
    status = db.Column(db.String(10))  # 'pending', 'active', 'closed'
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    
    user = db.relationship("User", back_populates="trades")
    votes = db.relationship("Vote", back_populates="trade")

class Vote(db.Model):
    __tablename__ = "votes"

    id = db.Column(db.Integer, primary_key=True, index=True)
    trade_id = db.Column(db.Integer, db.ForeignKey("trades.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    vote = db.Column(db.Boolean)  # True for yes, False for no
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship("User", back_populates="votes")
    trade = db.relationship("Trade", back_populates="votes")

class TradeAcceptance(db.Model):
    __tablename__ = "trade_acceptances"

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trade_id = db.Column(db.Integer, db.ForeignKey("trades.id"), nullable=False)
    allocation_amount = db.Column(db.Float, nullable=True)  # For BUY
    allocation_shares = db.Column(db.Integer, nullable=True)  # For SELL
    status = db.Column(db.String(10), nullable=False)  # 'ACCEPTED' or 'DENIED'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserPosition(db.Model):
    __tablename__ = "user_positions"

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 