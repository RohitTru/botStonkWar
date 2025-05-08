"""
Portfolio and brokerage summary models for StockBot brokerage handler.
"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class HistoricalPosition(db.Model):
    __tablename__ = 'historical_positions'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    shares_owned = db.Column(db.Numeric(10, 4), nullable=False)
    average_price = db.Column(db.Numeric(10, 2), nullable=False)
    market_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_value = db.Column(db.Numeric(15, 2), nullable=False)
    unrealized_pnl = db.Column(db.Numeric(15, 2), nullable=False)
    recorded_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BrokerageSummary(db.Model):
    __tablename__ = 'brokerage_summary'
    id = db.Column(db.BigInteger, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    total_shares = db.Column(db.Numeric(10, 4), nullable=False)
    average_price = db.Column(db.Numeric(10, 2), nullable=False)
    current_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_value = db.Column(db.Numeric(15, 2), nullable=False)
    unrealized_pnl = db.Column(db.Numeric(15, 2), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('symbol', name='unique_symbol'),) 