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

@main_bp.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@main_bp.route('/api/status')
def status():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    # Get scraper status
    scraper_status = "Running" if current_app.scraper_manager and current_app.scraper_manager.running else "Stopped"
    
    # Check database connection
    db_connected = db.check_connection()
    
    # Get recent articles with pagination
    articles, total_count = db.get_recent_articles(limit=per_page, offset=(page-1)*per_page)
    
    # Get scraping logs
    logs = db.get_scraping_logs(limit=50)  # Get last 50 logs
    
    # Calculate scraping statistics for the last hour
    stats = db.get_scraping_stats(hours=1)
    
    return jsonify({
        'status': scraper_status,
        'db_connected': db_connected,
        'articles_count': total_count,
        'recent_articles': articles,
        'scraping_logs': logs,
        'scraping_stats': stats
    })

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