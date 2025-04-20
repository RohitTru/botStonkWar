from flask import Blueprint, jsonify, render_template
from app import db, scraper_manager
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
        # Get scraper status from manager
        scraper_status = scraper_manager.get_status()
        status_text = "Running" if scraper_status['running'] else "Stopped"
        
        # Get article count
        article_count = article_service.get_article_count()
        
        # Get database status
        try:
            db.session.execute('SELECT 1')
            db_status = "Connected"
        except Exception:
            db_status = "Disconnected"
        
        # Get recent articles
        recent_articles = article_service.get_recent_articles(limit=10)
        
        # Get recent logs
        logs = logger.get_recent_logs(limit=20)
        
        return jsonify({
            'status': status_text,
            'articles_count': article_count,
            'db_status': db_status,
            'recent_articles': recent_articles,
            'logs': logs,
            'active_scrapers': scraper_status['active_scrapers']
        })
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/health')
def health():
    return jsonify(status="healthy") 