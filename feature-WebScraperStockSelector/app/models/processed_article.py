from app import db
from datetime import datetime

class ProcessedArticle(db.Model):
    __tablename__ = 'processed_articles'
    
    id = db.Column(db.Integer, primary_key=True)
    raw_article_id = db.Column(db.Integer, db.ForeignKey('raw_articles.id'), nullable=False)
    processed_content = db.Column(db.Text)
    processed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    raw_article = db.relationship('RawArticle', backref=db.backref('processed_article', uselist=False)) 