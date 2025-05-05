from flask import Blueprint, render_template, jsonify, request
import logging
from datetime import datetime
from decimal import Decimal
from database import Database
from sentiment_analyzer import SentimentAnalyzer
from analyzer_manager import AnalyzerManager

def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def serialize_decimal(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

routes = Blueprint('routes', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = Database()
analyzer = SentimentAnalyzer()
analyzer_manager = AnalyzerManager(db)

@routes.route('/')
def dashboard():
    """Render the main dashboard."""
    return render_template('dashboard.html')

@routes.route('/api/dashboard_stats')
def get_dashboard_stats():
    """Get current dashboard statistics"""
    try:
        stats = {
            "total_articles": db.get_analyzed_count(),
            "bullish_count": db.get_sentiment_count("bullish"),
            "bearish_count": db.get_sentiment_count("bearish"),
            "pending_count": db.get_unanalyzed_article_count(),
            # Bullish/Bearish ratios
            "sentiment_1h": db.get_sentiment_ratio_timewindow(1),
            "sentiment_1d": db.get_sentiment_ratio_today(),
            "sentiment_7d": db.get_sentiment_ratio_timewindow(168),
            "sentiment_30d": db.get_sentiment_ratio_timewindow(720)
        }
        return jsonify({
            "status": "success",
            "data": stats
        })
    except Exception as e:
        logging.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@routes.route('/api/recent_analyses')
def get_recent_analyses():
    """Get recent sentiment analyses with pagination"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        sort_by = request.args.get('sort', 'analyzed')  # Default to sorting by analysis time
        
        # Validate sort parameter
        if sort_by not in ['analyzed', 'published']:
            sort_by = 'analyzed'
        
        offset = (page - 1) * limit
        
        analyses = db.get_recent_analyses(limit=limit, offset=offset, sort_by=sort_by)
        
        # Serialize datetime and decimal objects
        serialized_analyses = []
        for analysis in analyses:
            serialized = {}
            for key, value in analysis.items():
                value = serialize_datetime(value)
                value = serialize_decimal(value)
                serialized[key] = value
            serialized_analyses.append(serialized)
        
        return jsonify({
            "status": "success",
            "data": serialized_analyses
        })
    except Exception as e:
        logging.error(f"Error getting recent analyses: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@routes.route('/api/stock_sentiment/<symbol>')
def stock_sentiment(symbol):
    """Get sentiment summary for a specific stock."""
    try:
        hours = int(request.args.get('hours', 24))
        summary = db.get_stock_sentiment_summary(symbol, hours)
        
        # Convert datetime objects and decimals in the summary
        if isinstance(summary, dict):
            for article in summary.get('articles', []):
                for key, value in article.items():
                    article[key] = serialize_datetime(value)
                    article[key] = serialize_decimal(value)
        
        return jsonify({
            "status": "success",
            "data": summary
        })
    except Exception as e:
        logging.error(f"Error fetching stock sentiment: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@routes.route('/api/analyze', methods=['POST'])
def analyze_pending():
    """Analyze pending articles."""
    try:
        articles = db.get_unanalyzed_articles(limit=10)
        results = []
        
        for article in articles:
            try:
                logging.info(f"\nProcessing article ID: {article['id']}")
                logging.info(f"Title: {article['title']}")
                
                # Prepare article data
                article_data = {
                    "id": article["id"],
                    "text": article["content"],
                    "stock_symbol": article["symbols"]
                }
                
                # Run sentiment analysis
                analysis = analyzer.analyze_article(article["content"], article_data)
                
                if "error" in analysis:
                    logging.error(f"Analysis failed: {analysis['error']}")
                    continue
                
                # Save to database
                db.save_sentiment_analysis(analysis)
                results.append(analysis)
                
            except Exception as e:
                logging.error(f"Error processing article {article['id']}: {str(e)}")
                continue
        
        return jsonify({
            "status": "success",
            "articles_analyzed": len(results),
            "results": results
        })
    except Exception as e:
        logging.error(f"Error analyzing articles: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@routes.route('/api/analyzer/pause', methods=['POST'])
def pause_analyzer():
    """Pause the sentiment analyzer"""
    try:
        analyzer_manager.pause()
        return jsonify({
            "status": "success",
            "message": "Analyzer paused successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@routes.route('/api/analyzer/resume', methods=['POST'])
def resume_analyzer():
    """Resume the sentiment analyzer"""
    try:
        analyzer_manager.resume()
        return jsonify({
            "status": "success",
            "message": "Analyzer resumed successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@routes.route('/api/analyzer/status', methods=['GET'])
def get_analyzer_status():
    """Get the current status of the analyzer"""
    try:
        status = analyzer_manager.get_status()
        return jsonify({
            "status": "success",
            "data": status
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500 