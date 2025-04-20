import os
from flask import Flask, jsonify, render_template
from app.models import db
from app.scrapers.base import BaseScraper
from app.services.stock_service import StockService
from app.services.article_service import ArticleService
from app.utils.logging import setup_logger

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_SCRAPING_DATABASE')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Setup logger
logger = setup_logger()

# Initialize services
stock_service = StockService()
article_service = ArticleService()

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def status():
    try:
        # Get scraper status
        scraper_status = "Running"  # This will be updated with actual scraper status
        
        # Get article count
        article_count = article_service.get_article_count()
        
        # Get database status
        db_status = "Connected"  # This will be updated with actual DB status
        
        # Get recent articles
        recent_articles = article_service.get_recent_articles(limit=10)
        
        # Get recent logs
        logs = logger.get_recent_logs(limit=20)
        
        return jsonify({
            'status': scraper_status,
            'articles_count': article_count,
            'db_status': db_status,
            'recent_articles': recent_articles,
            'logs': logs
        })
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify(status="healthy")

if __name__ == '__main__':
    app_port = int(os.getenv("APP_PORT", 5000))
    app.run(host='0.0.0.0', port=app_port)