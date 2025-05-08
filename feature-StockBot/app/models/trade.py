"""
Trade-related models for StockBot brokerage handler.
"""
from app.database import db
from datetime import datetime

class TradeNotification(db.Model):
    __tablename__ = 'trade_notifications'
    id = db.Column(db.BigInteger, primary_key=True)
    recommendation_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    action = db.Column(db.String(4), nullable=False)  # 'BUY' or 'SELL'
    status = db.Column(db.String(20), nullable=False)  # 'PENDING', 'CONFIRMED', etc.
    amount = db.Column(db.Numeric(10, 2))
    shares = db.Column(db.Numeric(10, 4))
    timeframe = db.Column(db.String(20), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TradeExecution(db.Model):
    __tablename__ = 'trade_executions'
    id = db.Column(db.BigInteger, primary_key=True)
    notification_id = db.Column(db.BigInteger, nullable=False)
    alpaca_order_id = db.Column(db.String(50), nullable=False)
    execution_price = db.Column(db.Numeric(10, 2), nullable=False)
    execution_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    total_shares = db.Column(db.Numeric(10, 4), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserAllocation(db.Model):
    __tablename__ = 'user_allocations'
    id = db.Column(db.BigInteger, primary_key=True)
    execution_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    shares = db.Column(db.Numeric(10, 4), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TradeAcceptance(db.Model):
    __tablename__ = 'trade_acceptances'
    id = db.Column(db.BigInteger, primary_key=True)
    trade_recommendation_id = db.Column(db.BigInteger, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    allocation_amount = db.Column(db.Numeric(15, 2), nullable=True)
    allocation_shares = db.Column(db.Numeric(15, 4), nullable=True)
    status = db.Column(db.String(16), nullable=False)  # ACCEPTED, DENIED, EXPIRED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('trade_recommendation_id', 'user_id', name='unique_acceptance'),)

class TradeExecutionLog(db.Model):
    __tablename__ = 'trade_execution_log'
    id = db.Column(db.BigInteger, primary_key=True)
    trade_recommendation_id = db.Column(db.BigInteger, nullable=False)
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(16), nullable=False)  # SUCCESS, FAILED
    details = db.Column(db.Text, nullable=True) 