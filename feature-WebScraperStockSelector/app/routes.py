from flask import Blueprint, jsonify, render_template, current_app, request
from datetime import datetime, timedelta
from app.utils.logging import setup_logger
from app.database import Database

# Create blueprint
main_bp = Blueprint('main', __name__)

# Setup logger
logger = setup_logger()

# Initialize database
db = Database()

@main_bp.route('/')
def index():
    """Render the dashboard."""
    return render_template('dashboard.html')

@main_bp.route('/api/status')
def status():
    try:
        # Get scraper status from manager
        scraper_manager = current_app.scraper_manager
        if scraper_manager:
            scraper_status = scraper_manager.get_status()
            status_text = "Running" if scraper_status['running'] else "Stopped"
            active_scrapers = scraper_status['active_scrapers']
        else:
            status_text = "Not Initialized"
            active_scrapers = []
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        
        # Get data from database
        articles, article_count = db.get_recent_articles(limit=per_page, offset=offset)
        scraping_logs = db.get_scraping_logs()
        scraping_stats = db.get_scraping_stats()
        
        return jsonify({
            'status': status_text,
            'articles_count': article_count,
            'recent_articles': articles,
            'scraping_logs': scraping_logs,
            'scraping_stats': scraping_stats,
            'active_scrapers': active_scrapers,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_pages': (article_count + per_page - 1) // per_page
            }
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/article/<path:article_url>')
def get_article(article_url):
    """Get full article details."""
    try:
        article = db.get_article_by_url(article_url)
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        return jsonify(article)
    except Exception as e:
        logger.error(f"Error getting article details: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/article/<path:article_url>', methods=['DELETE'])
def delete_article(article_url):
    """Delete an article and prevent it from being re-scraped."""
    try:
        if db.mark_article_deleted(article_url):
            # Update the scraper manager's seen URLs if available
            scraper_manager = current_app.scraper_manager
            if scraper_manager and hasattr(scraper_manager, 'yahoo_finance_scraper'):
                scraper_manager.yahoo_finance_scraper.seen_urls.add(article_url)
            return jsonify({'status': 'success', 'message': 'Article deleted successfully'})
        else:
            return jsonify({'error': 'Failed to delete article'}), 500
    except Exception as e:
        logger.error(f"Error deleting article: {e}")
        return jsonify({'error': str(e)}), 500

@main_bp.route('/health')
def health():
    return jsonify(status="healthy") 