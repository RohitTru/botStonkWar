from app import db
from datetime import datetime

class Stock(db.Model):
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(255))
    sector = db.Column(db.String(255))
    industry = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    raw_articles = db.relationship('RawArticle', backref='stock', lazy=True)
    
    def __repr__(self):
        return f'<Stock {self.symbol}>' 