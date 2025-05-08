"""
UserPosition model for tracking user stock holdings.
"""
from app.database import db
from datetime import datetime

class UserPosition(db.Model):
    __tablename__ = 'user_positions'
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    shares_owned = db.Column(db.Numeric(10, 4), nullable=False)
    average_buy_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'symbol', name='unique_user_position'),) 