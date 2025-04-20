from app import db
from datetime import datetime

class RawArticle(db.Model):
    __tablename__ = 'raw_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    source = db.Column(db.String(255))
    url = db.Column(db.String(2048))
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    published_at = db.Column(db.DateTime)
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock = db.relationship('Stock', backref=db.backref('articles', lazy=True)) 