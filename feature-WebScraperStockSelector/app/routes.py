from flask import Blueprint, jsonify, render_template
from app import db
from app.services.stock_service import StockService
from app.services.article_service import ArticleService
from app.utils.logging import setup_logger

# Create blueprint
main_bp = Blueprint('main', __name__)

# Setup logger
logger = setup_logger()

# Initialize services
stock_service = StockService()
article_service = ArticleService()

@main_bp.route('/')
def index():
    return render_template('dashboard.html')

@main_bp.route('/api/status')
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

@main_bp.route('/health')
def health():
    return jsonify(status="healthy") 