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

load_dotenv()

app = Flask(__name__)

# Database connection using Docker environment variables
DB_USER = os.getenv('MYSQL_USER')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD')
DB_HOST = os.getenv('MYSQL_HOST')
DB_NAME = os.getenv('MYSQL_DATABASE')

app.logger.info(f'Connecting to database at {DB_HOST}')

engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')
Session = sessionmaker(bind=engine)

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
    with engine.connect() as conn:
        window_start = (datetime.utcnow() - timedelta(minutes=FETCH_WINDOW_MINUTES)).strftime('%Y-%m-%d %H:%M:%S')
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
        result = conn.execute(query, {'window_start': window_start})
        articles = []
        sentiment_scores = {}
        for row in result:
            article = {
                'id': row[0],
                'title': row[1],
                'validated_symbols': json.loads(row[2]) if row[2] else [],
                'published_date': row[3].isoformat() if row[3] else None
            }
            articles.append(article)
            sentiment_scores[row[0]] = {
                'sentiment_score': float(row[4]),
                'confidence_score': float(row[5]),
                'prediction': row[6]
            }
        print(f"Fetched {len(articles)} articles from DB for strategy analysis (window: {window_start} to now).")
        return {
            'articles': articles,
            'sentiment_scores': sentiment_scores
        }

@app.route('/')
def index():
    print("Endpoint: / called")
    return render_template('index.html')

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
    
    # Always fetch and run strategies before returning recommendations
    strategy_data = fetch_strategy_data()
    new_recs = strategy_manager.run_all_strategies(strategy_data)
    
    # Insert new recommendations into MySQL
    for rec in new_recs:
        trade_db.insert(rec)
    
    # Fetch all recommendations from MySQL for the dashboard
    min_confidence = float(request.args.get('min_confidence', 0.0))
    timeframe = request.args.get('timeframe')
    
    # Get recommendations with pagination
    per_page = 10
    all_recs = trade_db.fetch_all()
    
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
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    paginated = filtered[start_idx:end_idx]
    
    return jsonify(paginated)

@app.route('/api/run-analysis', methods=['POST'])
def run_analysis():
    print("Endpoint: /api/run-analysis called")
    data = request.json
    recommendations = strategy_manager.run_all_strategies(data)
    return jsonify({
        'status': 'success',
        'recommendations': recommendations
    })

@app.route('/api/dashboard-data')
def get_dashboard_data():
    print("Endpoint: /api/dashboard-data called")
    try:
        print("Calling fetch_strategy_data() from dashboard-data endpoint.")
        strategy_data = fetch_strategy_data()
        print("Calling run_all_strategies() from dashboard-data endpoint.")
        recommendations = strategy_manager.run_all_strategies(strategy_data)
        strategies = strategy_manager.get_all_strategies()
        metrics = {
            'total_recommendations': len(recommendations),
            'buy_signals': len([r for r in recommendations if r['action'] == 'buy']),
            'sell_signals': len([r for r in recommendations if r['action'] == 'sell']),
            'high_confidence_signals': len([r for r in recommendations if r['confidence'] >= 0.8])
        }
        return jsonify({
            'status': 'success',
            'recommendations': recommendations,
            'strategies': strategies,
            'metrics': metrics
        })
    except Exception as e:
        print(f"Error in dashboard-data endpoint: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
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
        all_strategies = strategy_manager.get_all_strategies()
        if not all_strategies:
            app.logger.warning("No strategies found in strategy manager")
            return jsonify([])
        
        # Get status for all strategies
        status = strategy_manager.get_strategy_status()
        
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
                'metrics': {
                    'health': 'Unknown',
                    'errors': None,
                    'last_error_time': None,
                    'total_runs': 0,
                    'total_recommendations': 0,
                    'all_time_success_rate': 0.0,
                    'hourly': {
                        'recommendations_generated': 0,
                        'articles_processed': 0,
                        'success_rate': 0.0,
                        'avg_confidence': 0.0
                    }
                }
            }
            
            # Copy existing metrics if they exist
            if isinstance(s.get('metrics'), dict):
                cleaned['metrics'].update(s['metrics'])
                
                # Ensure hourly metrics exist
                if isinstance(s['metrics'].get('hourly'), dict):
                    cleaned['metrics']['hourly'].update(s['metrics']['hourly'])
            
            cleaned_status.append(cleaned)
        
        app.logger.info(f"Returning status for {len(cleaned_status)} strategies")
        return jsonify(cleaned_status)
        
    except Exception as e:
        app.logger.error(f"Error getting strategy status: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5008))
    app.run(host='0.0.0.0', port=port)