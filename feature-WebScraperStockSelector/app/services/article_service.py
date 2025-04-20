from app.models import db, RawArticle, ProcessedArticle
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class ArticleService:
    def __init__(self):
        self.logger = logger

    def save_raw_article(self, stock_id, source, url, title, content, published_at=None):
        """Save a raw article to the database."""
        try:
            article = RawArticle(
                stock_id=stock_id,
                source=source,
                url=url,
                title=title,
                content=content,
                published_at=published_at or datetime.utcnow()
            )
            db.session.add(article)
            db.session.commit()
            self.logger.info(f"Saved raw article: {title}")
            return article
        except Exception as e:
            self.logger.error(f"Error saving raw article: {str(e)}")
            db.session.rollback()
            return None

    def save_processed_article(self, raw_article_id, processed_content):
        """Save a processed article to the database."""
        try:
            processed = ProcessedArticle(
                raw_article_id=raw_article_id,
                processed_content=processed_content
            )
            db.session.add(processed)
            db.session.commit()
            self.logger.info(f"Saved processed article for raw article ID: {raw_article_id}")
            return processed
        except Exception as e:
            self.logger.error(f"Error saving processed article: {str(e)}")
            db.session.rollback()
            return None

    def get_recent_articles(self, limit=10):
        """Get recent articles with their associated stock information."""
        try:
            articles = RawArticle.query.join(Stock).order_by(
                RawArticle.published_at.desc()
            ).limit(limit).all()
            
            return [{
                'stock': article.stock.symbol,
                'title': article.title,
                'source': article.source,
                'date': article.published_at.strftime('%Y-%m-%d %H:%M:%S')
            } for article in articles]
        except Exception as e:
            self.logger.error(f"Error getting recent articles: {str(e)}")
            return []

    def get_article_count(self):
        """Get the total count of articles in the database."""
        try:
            return RawArticle.query.count()
        except Exception as e:
            self.logger.error(f"Error getting article count: {str(e)}")
            return 0

    def get_articles_by_stock(self, stock_id, days=7):
        """Get articles for a specific stock within a time period."""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            return RawArticle.query.filter_by(
                stock_id=stock_id
            ).filter(
                RawArticle.published_at >= start_date
            ).order_by(
                RawArticle.published_at.desc()
            ).all()
        except Exception as e:
            self.logger.error(f"Error getting articles for stock {stock_id}: {str(e)}")
            return [] 