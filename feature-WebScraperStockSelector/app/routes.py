from flask import Blueprint, jsonify, render_template, current_app, request, json
from datetime import datetime, timedelta
from app.utils.logging import setup_logger
from app.database import Database
from decimal import Decimal

# Create blueprint
main_bp = Blueprint('main', __name__)

# Setup logger
logger = setup_logger()

# Initialize database
db = Database()

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
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Get scraper status
        scraper_status = "Running" if current_app.scraper_manager and current_app.scraper_manager.running else "Error"
        
        # Check database connection
        db_connected = db.check_connection()
        
        # Get recent articles with pagination
        articles, total_count = db.get_recent_articles(limit=per_page, offset=(page-1)*per_page)
        
        # Calculate pagination info
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        # Format dates for JSON serialization
        for article in articles:
            if article.get('published_date'):
                article['published_date'] = article['published_date'].isoformat()
            if article.get('scraped_date'):
                article['scraped_date'] = article['scraped_date'].isoformat()
        
        # Get scraping logs
        logs = db.get_scraping_logs(limit=50)  # Get last 50 logs
        
        # Format dates in logs and ensure all fields are present
        formatted_logs = []
        for log in logs:
            formatted_log = {
                'timestamp': log['timestamp'].isoformat() if log.get('timestamp') else None,
                'status': log.get('status', 'UNKNOWN'),
                'source_type': log.get('source_type', ''),
                'url': log.get('url', ''),
                'error_message': log.get('error_message', '')
            }
            formatted_logs.append(formatted_log)
        
        # Calculate scraping statistics for the last hour
        stats = db.get_scraping_stats(hours=1)
        
        response_data = {
            'status': scraper_status,
            'db_connected': db_connected,
            'articles_count': total_count,
            'recent_articles': articles,
            'scraping_logs': formatted_logs,
            'scraping_stats': stats,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_pages': total_pages,
                'total_items': total_count,
                'has_next': has_next,
                'has_prev': has_prev
            }
        }
        
        return current_app.response_class(
            json.dumps(response_data, cls=CustomJSONEncoder),
            mimetype='application/json'
        )
    except Exception as e:
        logger.error(f"Error in status route: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'Error',
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
                'page': 1,
                'per_page': per_page,
                'total_pages': 0,
                'total_items': 0,
                'has_next': False,
                'has_prev': False
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

@main_bp.route('/api/scraper/control', methods=['POST'])
def control_scraper():
    """Control the scraper state (pause/resume)"""
    try:
        action = request.json.get('action')
        if action == 'pause':
            if current_app.scraper_manager:
                current_app.scraper_manager.pause()
                return jsonify({'status': 'success', 'message': 'Scraper paused'})
        elif action == 'resume':
            if current_app.scraper_manager:
                current_app.scraper_manager.resume()
                return jsonify({'status': 'success', 'message': 'Scraper resumed'})
        return jsonify({'status': 'error', 'message': 'Invalid action'}), 400
    except Exception as e:
        logger.error(f"Error controlling scraper: {str(e)}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500

@main_bp.route('/api/scraper/state')
def get_scraper_state():
    """Get the current state of the scraper"""
    try:
        if current_app.scraper_manager:
            return jsonify({
                'running': current_app.scraper_manager.running,
                'paused': current_app.scraper_manager.paused if hasattr(current_app.scraper_manager, 'paused') else False
            })
        return jsonify({'running': False, 'paused': False})
    except Exception as e:
        logger.error(f"Error getting scraper state: {str(e)}", exc_info=True)
        return jsonify({'running': False, 'paused': False}), 500 