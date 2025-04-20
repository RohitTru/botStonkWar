from app import db
from datetime import datetime

class Article(db.Model):
    __tablename__ = 'articles'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    title = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(1000), unique=True, nullable=False)
    source = db.Column(db.String(100), nullable=False)
    published_at = db.Column(db.DateTime)
    content = db.Column(db.Text)
    summary = db.Column(db.Text)
    sentiment_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    analysis = db.relationship('Analysis', backref='article', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<Article {self.title[:50]}...>' 