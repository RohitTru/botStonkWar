from datetime import datetime
from app import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, index=True)
    username = db.Column(db.String(80), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    balance = db.Column(db.Float, default=10000.0)
    
    votes = db.relationship("Vote", back_populates="user")

class Trade(db.Model):
    __tablename__ = "trades"

    id = db.Column(db.Integer, primary_key=True, index=True)
    strategy_id = db.Column(db.Integer, db.ForeignKey("trading_strategies.id"), nullable=True)
    stock_symbol = db.Column(db.String(10), index=True, nullable=False)
    trade_type = db.Column(db.Enum('BUY', 'SELL'), nullable=False)
    status = db.Column(db.Enum('PROPOSED', 'APPROVED', 'REJECTED', 'EXECUTED', 'CLOSED'), nullable=False)
    entry_price = db.Column(db.Numeric(10, 2), nullable=True)
    exit_price = db.Column(db.Numeric(10, 2), nullable=True)
    quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
    executed_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    
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

class TradeRecommendation(db.Model):
    __tablename__ = "trade_recommendations"

    id = db.Column(db.BigInteger, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    action = db.Column(db.String(10), nullable=False)
    confidence = db.Column(db.Float)
    reasoning = db.Column(db.Text)
    timeframe = db.Column(db.String(20))
    meta_data = db.Column('metadata', db.JSON)
    created_at = db.Column(db.DateTime)
    strategy_name = db.Column(db.String(50))
    trade_time = db.Column(db.DateTime)
    live_price = db.Column(db.Float)
    live_change_percent = db.Column(db.Float)
    live_volume = db.Column(db.BigInteger)
    status = db.Column(db.String(20), nullable=False, default='PENDING')
    amount = db.Column(db.Numeric(10,2), nullable=False, default=0.00)
    shares = db.Column(db.Numeric(10,4), nullable=False, default=0.0000)
    expires_at = db.Column(db.DateTime, nullable=False)
    required_acceptances = db.Column(db.Integer, nullable=False, default=1)
    updated_at = db.Column(db.DateTime)

class TradeAcceptance(db.Model):
    __tablename__ = "trade_acceptances"

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trade_id = db.Column(db.BigInteger, db.ForeignKey("trade_recommendations.id"), nullable=False)
    allocation_amount = db.Column(db.Float, nullable=True)  # For BUY
    allocation_shares = db.Column(db.Float, nullable=True)  # For SELL
    status = db.Column(db.String(10), nullable=False)  # 'ACCEPTED' or 'DENIED'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserPosition(db.Model):
    __tablename__ = "user_positions"

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    shares = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TradingStrategy(db.Model):
    __tablename__ = "trading_strategies"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text) 