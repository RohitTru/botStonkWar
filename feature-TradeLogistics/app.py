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
    app.logger.info("Registering strategies...")
    strategies = [
        (ShortTermVolatileStrategy(confidence_threshold=0.8), "Short Term Volatile"),
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
    
    for strategy, name in strategies:
        current_state = trade_db.get_strategy_activation(strategy.name)
        app.logger.info(f"Registering strategy {strategy.name} with current state: {current_state}")
        strategy_manager.register_strategy(strategy, active=current_state)

register_strategies()

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
def set_strategy_activation():
    data = request.json
    name = data.get('name')
    active = data.get('active')
    app.logger.info(f"Setting strategy {name} activation to {active}")
    
    try:
        strategy_manager.set_active(name, active)
        current_state = strategy_manager.get_active(name)
        app.logger.info(f"Strategy {name} activation set to {current_state}")
        return jsonify({
            "status": "success",
            "name": name,
            "active": current_state
        })
    except Exception as e:
        app.logger.error(f"Error setting strategy activation: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

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
    try:
        strategies = strategy_manager.get_all_strategies()
        app.logger.info(f"Strategy status: {json.dumps(strategies)}")
        return jsonify({"strategies": strategies})
    except Exception as e:
        app.logger.error(f"Error getting strategy status: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
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