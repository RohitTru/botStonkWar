import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template
import requests
import pandas as pd
from collections import defaultdict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import json
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

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

# Database configuration from environment variables
DB_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'botstonkwar_scraping_db')
}

# Create SQLAlchemy engine
try:
    DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}/{DB_CONFIG['database']}"
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    # Test the connection
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    app.logger.info('Database connection established successfully')
except Exception as e:
    app.logger.error(f'Error connecting to database: {str(e)}')
    raise

class TradingStrategy:
    def __init__(self, name, description, threshold=0.7):
        self.name = name
        self.description = description
        self.threshold = threshold
        self.signals = []
        self.success_count = 0
        self.total_signals = 0
        self.session = Session()

    def get_success_rate(self):
        if self.total_signals == 0:
            return 0
        return (self.success_count / self.total_signals) * 100

    def add_signal(self, signal):
        self.signals.append(signal)
        self.total_signals += 1
        app.logger.info(f'New signal added for {self.name}: {signal}')

class SentimentMomentumStrategy(TradingStrategy):
    def analyze(self):
        signals = []
        try:
            # Query recent sentiment analyses with validated symbols
            query = """
            SELECT 
                a.validated_symbols,
                sa.sentiment_score,
                sa.confidence_score,
                sa.prediction,
                a.title,
                a.published_date,
                sa.analysis_timestamp
            FROM sentiment_analysis sa
            JOIN articles a ON sa.article_id = a.id
            WHERE 
                a.validated_symbols IS NOT NULL
                AND sa.analysis_timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                AND sa.confidence_score >= :threshold
            ORDER BY sa.analysis_timestamp DESC
            """
            
            results = self.session.execute(text(query), {'threshold': self.threshold})
            
            # Group sentiments by symbol
            symbol_sentiments = defaultdict(list)
            for row in results:
                symbols = json.loads(row.validated_symbols)
                for symbol in symbols:
                    symbol_sentiments[symbol].append({
                        'score': row.sentiment_score,
                        'confidence': row.confidence_score,
                        'prediction': row.prediction,
                        'title': row.title,
                        'timestamp': row.analysis_timestamp
                    })
            
            app.logger.info(f'Analyzed {len(symbol_sentiments)} symbols for sentiment')
            
            # Generate signals for symbols with strong sentiment
            for symbol, analyses in symbol_sentiments.items():
                if len(analyses) < 3:  # Require at least 3 mentions
                    continue
                    
                # Calculate weighted average sentiment
                weighted_sentiment = sum(a['score'] * a['confidence'] for a in analyses) / sum(a['confidence'] for a in analyses)
                
                if weighted_sentiment > self.threshold:
                    signal = {
                        'symbol': symbol,
                        'type': 'BUY',
                        'strategy': self.name,
                        'price': 'Market',
                        'timestamp': datetime.now(),
                        'reason': f"Strong positive sentiment detected (score: {weighted_sentiment:.2f} from {len(analyses)} articles)"
                    }
                    signals.append(signal)
                    app.logger.info(f'Generated BUY signal for {symbol}: {weighted_sentiment:.2f}')
                elif weighted_sentiment < -self.threshold:
                    signal = {
                        'symbol': symbol,
                        'type': 'SELL',
                        'strategy': self.name,
                        'price': 'Market',
                        'timestamp': datetime.now(),
                        'reason': f"Strong negative sentiment detected (score: {weighted_sentiment:.2f} from {len(analyses)} articles)"
                    }
                    signals.append(signal)
                    app.logger.info(f'Generated SELL signal for {symbol}: {weighted_sentiment:.2f}')
            
        except Exception as e:
            app.logger.error(f'Error in sentiment analysis: {str(e)}')
            self.session.rollback()
        
        return signals

class VolumeStrategy(TradingStrategy):
    def analyze(self):
        # This would need integration with a real-time market data feed
        # For now, we'll focus on the sentiment strategy
        return []

# Initialize strategies
TRADING_STRATEGIES = {
    'sentiment': SentimentMomentumStrategy(
        "Sentiment-Based Momentum",
        "Uses sentiment analysis to identify trending stocks"
    ),
    'volume': VolumeStrategy(
        "Volume Spike Detection",
        "Identifies unusual trading volume patterns"
    )
}

def get_strategy_performance(strategy, days=30):
    """Get historical performance data for a strategy"""
    session = Session()
    
    # This is a placeholder - you'll need to implement actual performance tracking
    # For now, we'll return simulated data
    now = datetime.now()
    timestamps = [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days, -1, -1)]
    performance = [75 + (i % 10) for i in range(days + 1)]  # Simulated performance data
    
    session.close()
    return timestamps, performance

def generate_trading_signals():
    """Generate real trading signals based on database data"""
    all_signals = []
    for strategy in TRADING_STRATEGIES.values():
        signals = strategy.analyze()
        all_signals.extend(signals)
    return all_signals

@app.route('/')
def index():
    signals = generate_trading_signals()
    buy_signals = [s for s in signals if s['type'] == 'BUY']
    sell_signals = [s for s in signals if s['type'] == 'SELL']
    
    # Get active users count
    session = Session()
    # This would need to be implemented based on your user tracking system
    users_following = 0
    session.close()
    
    strategies_status = []
    for strategy in TRADING_STRATEGIES.values():
        strategies_status.append({
            "id": id(strategy),
            "name": strategy.name,
            "description": strategy.description,
            "status": "Active",
            "status_class": "status-active",
            "success_rate": strategy.get_success_rate(),
            "last_signal": "Just now" if signals else "No recent signals"
        })

    return render_template('dashboard.html',
                         last_update=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         active_strategies=len(TRADING_STRATEGIES),
                         success_rate=75,  # This should be calculated based on historical performance
                         users_following=users_following,
                         pending_signals=len(signals),
                         strategies=strategies_status,
                         buy_signals=buy_signals,
                         sell_signals=sell_signals)

@app.route('/api/dashboard-data')
def dashboard_data():
    signals = generate_trading_signals()
    
    # Get performance data for each strategy
    performance_data = {"strategies": []}
    for strategy in TRADING_STRATEGIES.values():
        timestamps, performance = get_strategy_performance(strategy)
        performance_data["strategies"].append({
            "name": strategy.name,
            "timestamps": timestamps,
            "performance": performance
        })
    
    return jsonify({
        "performance": performance_data,
        "strategies": [s for s in TRADING_STRATEGIES.values()],
        "metrics": {
            "active_strategies": len(TRADING_STRATEGIES),
            "success_rate": 75,  # Should be calculated from actual performance
            "users_following": 0,  # Implement based on your user system
            "pending_signals": len(signals)
        }
    })

@app.route('/health')
def health():
    return jsonify(status="healthy")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5009))
    app.run(host='0.0.0.0', port=port)