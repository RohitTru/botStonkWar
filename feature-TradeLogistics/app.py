import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import logging
from logging.handlers import RotatingFileHandler
from decision_engine.manager import StrategyManager
from decision_engine.strategies.short_term import ShortTermVolatileStrategy
from decision_engine.strategies.consensus import SentimentConsensusStrategy
from decision_engine.strategies.reversal import SentimentReversalStrategy
from dotenv import load_dotenv
from decision_engine.models.trade_mysql import TradeRecommendationMySQL
from decision_engine.strategies.obscure import ObscureStockDetectorStrategy
from decision_engine.strategies.momentum import SentimentMomentumStrategy
from decision_engine.strategies.price_confirmation import SentimentPriceConfirmationStrategy
from decision_engine.strategies.mean_reversion import MeanReversionFilterStrategy
from decision_engine.strategies.volume_spike import VolumeSpikeSentimentStrategy
from decision_engine.strategies.news_breakout import NewsDrivenBreakoutStrategy
from decision_engine.strategies.sentiment_divergence import SentimentDivergenceStrategy
from decision_engine.alpaca_ws_price_service import price_service
import redis
from rq import Queue
from rq_scheduler import Scheduler
from functools import lru_cache
import time
from threading import Thread
import threading
import random  # Add at the top with other imports
from sqlalchemy.pool import QueuePool  # Add this import

load_dotenv()

app = Flask(__name__)

# Database connection with connection pooling
db_url = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}"
engine = create_engine(
    db_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

# Redis connection for task queue (without decode_responses for RQ)
redis_conn = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    socket_timeout=5,
    socket_connect_timeout=5
)

# Redis connection for regular operations (with decode_responses)
redis_regular = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True,
    encoding='utf-8',
    charset='utf-8',
    errors='replace',
    socket_timeout=5,
    socket_connect_timeout=5
)

# Create RQ queue
task_queue = Queue('trade_tasks', connection=redis_conn)

# Create scheduler
scheduler = Scheduler(queue=task_queue, connection=redis_conn)

# Initialize trade recommendations with MySQL
trade_db = TradeRecommendationMySQL(engine)
strategy_manager = StrategyManager(trade_db)

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

file_handler = RotatingFileHandler('logs/trade_brain.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Trade Brain startup')

# Register strategies
def register_strategies():
    """Register all trading strategies with proper error handling."""
    app.logger.info("Starting strategy registration...")
    
    strategies = [
        (ShortTermVolatileStrategy(), "Short Term Volatile"),
        (SentimentConsensusStrategy(confidence_threshold=0.8, min_articles=3, window_minutes=30), "Sentiment Consensus"),
        (SentimentReversalStrategy(confidence_threshold=0.8, lookback=10, cluster=2), "Sentiment Reversal"),
        (ObscureStockDetectorStrategy(), "Obscure Stock Detector"),
        (SentimentMomentumStrategy(), "Sentiment Momentum"),
        (SentimentPriceConfirmationStrategy(), "Price Confirmation"),
        (MeanReversionFilterStrategy(), "Mean Reversion"),
        (VolumeSpikeSentimentStrategy(), "Volume Spike"),
        (NewsDrivenBreakoutStrategy(), "News Breakout"),
        (SentimentDivergenceStrategy(), "Sentiment Divergence")
    ]
    
    registered_count = 0
    error_count = 0
    
    for strategy, description in strategies:
        try:
            # Ensure strategy has required attributes
            if not hasattr(strategy, 'name') or not strategy.name:
                strategy.name = strategy.__class__.__name__
            
            if not hasattr(strategy, 'description') or not strategy.description:
                strategy.description = description
            
            # Get current activation state from DB
            try:
                current_state = trade_db.get_strategy_activation(strategy.name)
            except Exception as db_error:
                app.logger.error(f"Database error getting activation state for {strategy.name}: {db_error}")
                current_state = True  # Default to active if DB fails
            
            if current_state is None:
                current_state = True
                try:
                    trade_db.set_strategy_activation(strategy.name, current_state)
                except Exception as db_error:
                    app.logger.error(f"Database error setting activation state for {strategy.name}: {db_error}")
            
            # Register the strategy
            strategy_manager.register_strategy(strategy, active=current_state)
            app.logger.info(f"Successfully registered strategy {strategy.name} ({description}) with state: {current_state}")
            registered_count += 1
            
        except Exception as e:
            error_count += 1
            app.logger.error(f"Error registering strategy {strategy.__class__.__name__}: {str(e)}", exc_info=True)
            continue
    
    app.logger.info(f"Strategy registration complete. {registered_count} registered, {error_count} failed.")
    if error_count > 0:
        app.logger.warning("Some strategies failed to register. Check logs for details.")
    
    return registered_count > 0  # Return True if at least one strategy was registered

# Register strategies when app starts
if not register_strategies():
    app.logger.error("No strategies were registered successfully!")

FETCH_WINDOW_MINUTES = 30  # Time window for live strategies

def fetch_strategy_data():
    """Fetch recent articles and sentiment data for strategy analysis."""
    try:
        with engine.connect() as conn:
            window_start = (datetime.utcnow() - timedelta(minutes=FETCH_WINDOW_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')
            
            # First check if we have any articles in the table
            count_query = text("SELECT COUNT(*) FROM articles")
            total_articles = conn.execute(count_query).scalar()
            app.logger.info(f"Total articles in database: {total_articles}")
            
            # Check sentiment analysis table
            sa_count_query = text("SELECT COUNT(*) FROM sentiment_analysis")
            total_sa = conn.execute(sa_count_query).scalar()
            app.logger.info(f"Total sentiment analyses in database: {total_sa}")
            
            # Get recent articles with sentiment
            query = text("""
                SELECT 
                    a.id,
                    a.title,
                    a.validated_symbols,
                    a.published_date,
                    sa.sentiment_score,
                    sa.confidence_score,
                    sa.prediction
                FROM sentiment_analysis sa
                JOIN articles a ON a.id = sa.article_id
                WHERE a.is_analyzed = TRUE
                  AND a.published_date >= :window_start
                ORDER BY a.published_date DESC
            """)
            
            # Log the query parameters
            app.logger.info(f"Fetching articles from {window_start} to now")
            
            result = conn.execute(query, {'window_start': window_start})
            articles = []
            sentiment_scores = {}
            
            for row in result:
                try:
                    article = {
                        'id': row[0],
                        'title': row[1],
                        'validated_symbols': json.loads(row[2]) if row[2] else [],
                        'published_date': row[3].isoformat() if row[3] else None
                    }
                    articles.append(article)
                    sentiment_scores[row[0]] = {
                        'sentiment_score': float(row[4]) if row[4] is not None else 0.0,
                        'confidence_score': float(row[5]) if row[5] is not None else 0.0,
                        'prediction': row[6]
                    }
                except Exception as e:
                    app.logger.error(f"Error processing row {row}: {str(e)}")
                    continue
            
            # Check recent articles
            recent_query = text("""
                SELECT COUNT(*)
                FROM articles
                WHERE published_date >= :window_start
            """)
            recent_count = conn.execute(recent_query, {'window_start': window_start}).scalar()
            app.logger.info(f"Total articles in time window: {recent_count}")
            
            # Check analyzed articles
            analyzed_query = text("""
                SELECT COUNT(*)
                FROM articles a
                JOIN sentiment_analysis sa ON a.id = sa.article_id
                WHERE a.published_date >= :window_start
                  AND a.is_analyzed = TRUE
            """)
            analyzed_count = conn.execute(analyzed_query, {'window_start': window_start}).scalar()
            app.logger.info(f"Analyzed articles in time window: {analyzed_count}")
            
            app.logger.info(f"Fetched {len(articles)} articles with sentiment scores from DB")
            if len(articles) == 0:
                app.logger.warning("No articles found with sentiment analysis in the time window")
            
            return {
                'articles': articles,
                'sentiment_scores': sentiment_scores
            }
            
    except Exception as e:
        app.logger.error(f"Error fetching strategy data: {str(e)}", exc_info=True)
        # Return empty data rather than failing
        return {
            'articles': [],
            'sentiment_scores': {}
        }

def gather_dashboard_data():
    try:
        # Get the latest job results
        latest_job = task_queue.get_jobs()[-1] if task_queue.get_jobs() else None
        if latest_job and latest_job.result:
            return latest_job.result

        # If no job results, gather data directly
        metrics = {
            'total_recommendations': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'last_updated': datetime.now().isoformat()
        }
        
        recommendations = []
        
        # Get active strategies
        active_strategies = strategy_manager.get_active_strategies()
        
        # Get all strategies with their status
        strategies = strategy_manager.get_strategy_status()
        
        # Fetch data for each active strategy
        for strategy in active_strategies:
            try:
                strategy_data = fetch_strategy_data()
                if not strategy_data:
                    continue
                    
                # Run strategy analysis
                results = strategy.analyze(strategy_data)
                
                # Update metrics
                metrics['total_recommendations'] += len(results)
                for result in results:
                    if result.get('signal') == 'BUY':
                        metrics['buy_signals'] += 1
                    elif result.get('signal') == 'SELL':
                        metrics['sell_signals'] += 1
                    else:
                        metrics['hold_signals'] += 1
                        
                    recommendations.append({
                        'symbol': result.get('symbol'),
                        'strategy': strategy.name,
                        'signal': result.get('signal'),
                        'confidence': result.get('confidence', 0),
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                app.logger.error(f"Error processing strategy {strategy.name}: {str(e)}")
                continue
                
        return {
            'metrics': metrics,
            'recommendations': recommendations,
            'strategies': strategies  # Add strategies to the response
        }
        
    except Exception as e:
        app.logger.error(f"Error gathering dashboard data: {str(e)}")
        return {
            'metrics': {
                'total_recommendations': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'hold_signals': 0,
                'last_updated': datetime.now().isoformat()
            },
            'recommendations': [],
            'strategies': []  # Add empty strategies list for error case
        }

# Replace old caches with unified dashboard cache
default_dashboard_cache = {
    'metrics': {
        'total_recommendations': 0,
        'buy_signals': 0,
        'sell_signals': 0,
        'hold_signals': 0,
        'last_updated': datetime.now().isoformat(),
        'recommendations_last_hour': 0
    },
    'recommendations': [],
    'strategies': []
}
_dashboard_cache = default_dashboard_cache.copy()
_dashboard_cache_lock = threading.Lock()

# Update the dashboard cache thread
def update_dashboard_cache():
    global _dashboard_cache
    while True:
        try:
            all_recs = trade_db.fetch_all()  # Fetch all recommendations, no time window
            now = datetime.utcnow()
            # Calculate metrics from all recommendations
            recs_last_hour = [
                r for r in all_recs
                if 'created_at' in r and isinstance(r['created_at'], str)
                and safe_fromisoformat(r['created_at']) is not None
                and (now - safe_fromisoformat(r['created_at'])).total_seconds() < 3600
            ]
            metrics = {
                'total_recommendations': len(all_recs),
                'buy_signals': sum(1 for r in all_recs if r.get('action') == 'buy'),
                'sell_signals': sum(1 for r in all_recs if r.get('action') == 'sell'),
                'hold_signals': sum(1 for r in all_recs if r.get('action') == 'hold'),
                'last_updated': now.isoformat(),
                'recommendations_last_hour': len(recs_last_hour)
            }
            strategies = strategy_manager.get_strategy_status()
            with _dashboard_cache_lock:
                _dashboard_cache = {
                    'metrics': metrics,
                    'recommendations': all_recs,
                    'strategies': strategies
                }
        except Exception as e:
            app.logger.error(f"Error updating dashboard cache: {str(e)}")
            with _dashboard_cache_lock:
                _dashboard_cache = default_dashboard_cache.copy()
        time.sleep(2.5 + random.random() * 0.5)

# Helper for robust fromisoformat
from datetime import datetime

def safe_fromisoformat(val):
    try:
        return datetime.fromisoformat(val)
    except Exception:
        return None

# Start the new background thread
cache_thread = Thread(target=update_dashboard_cache, daemon=True)
cache_thread.start()

# Update /api/dashboard-data endpoint
def get_dashboard_data():
    with _dashboard_cache_lock:
        return jsonify(_dashboard_cache)
app.add_url_rule('/api/dashboard-data', 'get_dashboard_data', get_dashboard_data)

@app.route('/')
def index():
    with _dashboard_cache_lock:
        data = _dashboard_cache.copy()
    ws_symbols = price_service.get_subscribed_symbols()
    return render_template('index.html', metrics=data['metrics'], strategies=data['strategies'], recommendations=data['recommendations'], ws_symbols=ws_symbols)

@app.route('/api/strategies')
def get_strategies():
    print("Endpoint: /api/strategies called")
    return jsonify(strategy_manager.get_all_strategies())

@app.route('/api/recommendations')
def get_recommendations():
    print("Endpoint: /api/recommendations called")
    
    # Get query parameters
    page = int(request.args.get('page', 1))
    filter_type = request.args.get('filter', 'all')
    strategy = request.args.get('strategy', '')
    min_confidence = float(request.args.get('min_confidence', 0.0))
    timeframe = request.args.get('timeframe')
    
    # Get recommendations from cache
    with _dashboard_cache_lock:
        all_recs = _dashboard_cache['recommendations']
    
    # Apply filters
    filtered = [r for r in all_recs if (
        (min_confidence == 0.0 or r['confidence'] >= min_confidence) and
        (not timeframe or r['timeframe'] == timeframe) and
        (not strategy or r['strategy_name'] == strategy) and
        (filter_type == 'all' or r['action'] == filter_type)
    )]
    
    # Sort by creation time, newest first
    filtered.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Paginate results
    per_page = 10
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated = filtered[start_idx:end_idx]
    
    return jsonify(paginated)

@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    try:
        # Enqueue the task
        job = task_queue.enqueue(
            'decision_engine.tasks.process_strategies',
            job_timeout='5m'
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Analysis started',
            'job_id': job.id
        })
    except Exception as e:
        app.logger.error(f"Error starting analysis: {str(e)}")
        return jsonify({
            'error': 'Failed to start analysis',
            'details': str(e)
        }), 500

@app.route('/health')
def health():
    print("Endpoint: /health called")
    return jsonify(status="healthy")

@app.route('/api/live-price', methods=['POST'])
def get_live_price():
    print(f"Endpoint: /api/live-price POST called")
    data = request.json
    symbol = data.get('symbol')
    action = data.get('action')
    strategy_name = data.get('strategy_name')
    created_at = data.get('created_at')
    from decision_engine.strategies.short_term import ShortTermVolatileStrategy
    strat = ShortTermVolatileStrategy()
    live_data = strat.fetch_live_price(symbol)
    # Update MySQL record
    trade_db.update_live_data(symbol, action, strategy_name, created_at, live_data)
    return jsonify(live_data)

@app.route('/api/strategy-activation', methods=['POST'])
def strategy_activation():
    """Set strategy activation state."""
    try:
        data = request.json
        name = data.get('name')
        active = data.get('active')
        if name is None or active is None:
            return jsonify({'error': 'Missing name or active state'}), 400
        strategy_manager.set_strategy_active(name, active)
        return jsonify({'status': 'success'})
    except Exception as e:
        app.logger.error(f"Error setting strategy activation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/strategy-activation', methods=['GET'])
def get_strategy_activation():
    return jsonify(trade_db.get_all_strategy_activation())

@app.route('/api/ws-subscribed-symbols')
def get_ws_subscribed_symbols():
    return jsonify({'symbols': price_service.get_subscribed_symbols()})

@app.route('/api/ws-subscribed-symbol-prices')
def ws_subscribed_symbol_prices():
    symbols = price_service.get_subscribed_symbols()
    prices = {}
    for symbol in symbols:
        price_data = price_service.get_price(symbol)
        prices[symbol] = price_data if price_data else {}
    return jsonify(prices)

@app.route('/api/strategy-status')
def strategy_status():
    """Get status of all strategies."""
    try:
        # First check if we have any strategies registered
        app.logger.info("Fetching strategy status - checking registered strategies")
        all_strategies = strategy_manager.get_all_strategies()
        if not all_strategies:
            app.logger.warning("No strategies found in strategy manager")
            return jsonify([])
        
        app.logger.info(f"Found {len(all_strategies)} registered strategies")
        
        # Get status for all strategies
        status = strategy_manager.get_strategy_status()
        app.logger.info(f"Retrieved status for {len(status)} strategies")
        
        # Log each strategy's status
        for s in status:
            app.logger.info(f"Strategy {s.get('name', 'Unknown')}: active={s.get('active', False)}, health={s.get('metrics', {}).get('health', 'Unknown')}")
        
        # Validate and clean up each status object
        cleaned_status = []
        for s in status:
            if not isinstance(s, dict):
                app.logger.error(f"Invalid strategy status object (not a dict): {s}")
                continue
                
            # Ensure required fields exist
            cleaned = {
                'name': s.get('name', 'Unknown'),
                'description': s.get('description', 'No description'),
                'active': s.get('active', False),
                'last_run': s.get('last_run'),
                'metrics': s.get('metrics', {})
            }
            cleaned_status.append(cleaned)
        
        app.logger.info(f"Returning {len(cleaned_status)} cleaned strategy status objects")
        return jsonify(cleaned_status)
        
    except Exception as e:
        app.logger.error(f"Error in strategy_status endpoint: {str(e)}", exc_info=True)
        return jsonify([])

@app.route('/api/db-health')
def check_db_health():
    try:
        # Try to execute a simple query
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            # Also check if our tables exist
            conn.execute(text("SELECT COUNT(*) FROM strategy_activation"))
            conn.execute(text("SELECT COUNT(*) FROM trade_recommendations"))
        return jsonify({
            "status": "connected",
            "message": "Database connection successful"
        })
    except Exception as e:
        app.logger.error(f"Database connection error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/job-status/<job_id>')
def get_job_status(job_id):
    try:
        job = task_queue.fetch_job(job_id)
        if not job:
            return jsonify({
                'error': 'Job not found'
            }), 404
            
        status = {
            'id': job.id,
            'status': job.get_status(),
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'ended_at': job.ended_at.isoformat() if job.ended_at else None,
            'result': job.result if job.result else None
        }
        
        return jsonify(status)
    except Exception as e:
        app.logger.error(f"Error getting job status: {str(e)}")
        return jsonify({
            'error': 'Failed to get job status',
            'details': str(e)
        }), 500

def schedule_periodic_tasks():
    try:
        # Schedule strategy processing every 5 minutes
        scheduler.schedule(
            scheduled_time=datetime.utcnow(),
            func='decision_engine.tasks.process_strategies',
            interval=300,  # 5 minutes
            repeat=None  # Run indefinitely
        )
        app.logger.info("Scheduled periodic tasks")
    except Exception as e:
        app.logger.error(f"Error scheduling tasks: {str(e)}")

# Schedule tasks on startup
schedule_periodic_tasks()

def run_strategies_live():
    while True:
        try:
            strategy_data = fetch_strategy_data()
            new_recs = strategy_manager.run_all_strategies(strategy_data)
            for rec in new_recs:
                trade_db.insert(rec)
        except Exception as e:
            app.logger.error(f"Error running live strategies: {str(e)}")
        time.sleep(2.5 + random.random() * 0.5)

# Start the live strategy runner thread
live_strat_thread = Thread(target=run_strategies_live, daemon=True)
live_strat_thread.start()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5008))
    app.run(host='0.0.0.0', port=port)