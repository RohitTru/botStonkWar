from flask import Blueprint, jsonify, render_template, current_app, request, json
from datetime import datetime, timedelta
from app.utils.logging import setup_logger
from app.database import Database
from decimal import Decimal
from app.scraper_manager import ScraperManager

# Create blueprint
main_bp = Blueprint('main', __name__)

# Setup logger
logger = setup_logger()

# Initialize database
db = Database()

# Initialize the scraper manager
scraper_manager = ScraperManager()

# Add the Yahoo Finance scraper
from app.scrapers.yahoo_finance import YahooFinanceScraper
scraper_manager.add_scraper('yahoo_finance', YahooFinanceScraper())

# Start the scraper manager
scraper_manager.run()

# Custom JSON encoder to handle Decimal objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

@main_bp.route('/')
def index():
    """Render the dashboard."""
    return render_template('dashboard.html')

@main_bp.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@main_bp.route('/api/status')
def status():
    """Get the current status of the scraper."""
    try:
        # Get scraper status
        scraper_status = scraper_manager.get_scraper_status('yahoo_finance')
        
        # Get database connection status
        db_connected = db.check_connection()
        
        if not db_connected:
            return jsonify({
                'status': 'Error',
                'error': 'Database disconnected',
                'db_connected': False,
                'articles_count': 0,
                'recent_articles': [],
                'scraping_logs': [],
                'scraping_stats': {
                    'total_attempts': 0,
                    'successful': 0,
                    'failed': 0,
                    'success_rate': 0
                },
                'pagination': {
                    'has_next': False
                }
            }), 500
        
        # Get article count
        articles_count = db.get_article_count()
        
        # Get recent articles
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        recent_articles = db.get_recent_articles(
            limit=per_page,
            offset=(page - 1) * per_page
        )
        
        # Get scraping logs
        scraping_logs = db.get_scraping_logs(limit=50)
        
        # Get scraping stats from ScraperManager
        scraping_stats = scraper_manager.get_scraper_metrics(hours=1)['total']
        
        return jsonify({
            'status': scraper_status,
            'paused': scraper_status == 'Paused',
            'db_connected': True,
            'articles_count': articles_count,
            'recent_articles': recent_articles,
            'scraping_logs': scraping_logs,
            'scraping_stats': scraping_stats,
            'pagination': {
                'has_next': len(recent_articles) == per_page,
                'page': page,
                'per_page': per_page
            }
        })
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({
            'status': 'Error',
            'error': str(e),
            'db_connected': False,
            'articles_count': 0,
            'recent_articles': [],
            'scraping_logs': [],
            'scraping_stats': {
                'total_attempts': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0
            },
            'pagination': {
                'has_next': False,
                'page': 1,
                'per_page': 10
            }
        }), 500

@main_bp.route('/api/article/<path:article_url>')
def get_article(article_url):
    """Get full article details."""
    try:
        article = db.get_article_by_url(article_url)
        if article:
            # Format dates for JSON serialization
            if article.get('published_date'):
                article['published_date'] = article['published_date'].isoformat()
            if article.get('scraped_date'):
                article['scraped_date'] = article['scraped_date'].isoformat()
            return jsonify(article)
        return jsonify({'error': 'Article not found'}), 404
    except Exception as e:
        logger.error(f"Error getting article: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/article/<path:article_url>', methods=['DELETE'])
def delete_article(article_url):
    """Delete an article and prevent it from being re-scraped."""
    try:
        if db.mark_article_deleted(article_url):
            return jsonify({'status': 'success'})
        return jsonify({'error': 'Failed to delete article'}), 400
    except Exception as e:
        logger.error(f"Error deleting article: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/toggle_scraper', methods=['POST'])
def toggle_scraper():
    """Toggle the scraper between paused and running states."""
    try:
        data = request.get_json()
        action = data.get('action', '').lower()
        
        if action == 'pause':
            success = scraper_manager.pause_scraper('yahoo_finance')
        elif action == 'resume':
            success = scraper_manager.resume_scraper('yahoo_finance')
        else:
            return jsonify({'success': False, 'error': 'Invalid action'}), 400
            
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to toggle scraper'}), 500
            
    except Exception as e:
        logger.error(f"Error toggling scraper: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 