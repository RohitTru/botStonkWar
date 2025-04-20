from app import db
from datetime import datetime
from .stock import Stock
from .article import Article
from .analysis import Analysis

__all__ = ['Stock', 'Article', 'Analysis']

class Stock(db.Model):
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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

class ProcessedArticle(db.Model):
    __tablename__ = 'processed_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    raw_article_id = db.Column(db.Integer, db.ForeignKey('raw_articles.id'), nullable=False)
    processed_content = db.Column(db.Text)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    raw_article = db.relationship('RawArticle', backref=db.backref('processed_article', uselist=False))

class SentimentAnalysis(db.Model):
    __tablename__ = 'sentiment_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    processed_article_id = db.Column(db.Integer, db.ForeignKey('processed_articles.id'), nullable=False)
    sentiment_score = db.Column(db.Float)
    confidence = db.Column(db.Float)
    analysis_type = db.Column(db.String(50))
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    processed_article = db.relationship('ProcessedArticle', backref=db.backref('sentiment_analysis', lazy=True))

class TechnicalAnalysis(db.Model):
    __tablename__ = 'technical_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    analysis_type = db.Column(db.String(50))
    value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock = db.relationship('Stock', backref=db.backref('technical_analysis', lazy=True)) 