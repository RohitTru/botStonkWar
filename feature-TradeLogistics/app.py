import os
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request
import requests
import pandas as pd
from collections import defaultdict
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import json
import logging
from logging.handlers import RotatingFileHandler
from decision_engine.manager import StrategyManager
from decision_engine.strategies.short_term import ShortTermVolatileStrategy
import asyncio
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
strategy_manager = StrategyManager()

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
strategy_manager.register_strategy(ShortTermVolatileStrategy(confidence_threshold=0.8))

# Database connection
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')

async def fetch_strategy_data():
    """Fetch and process data from database for strategy analysis."""
    with engine.connect() as conn:
        # Get recent articles with their sentiment analysis
        query = text("""
            SELECT 
                a.id,
                a.title,
                a.validated_symbols,
                a.published_date,
                sa.sentiment_score,
                sa.confidence_score,
                sa.prediction
            FROM articles a
            JOIN sentiment_analysis sa ON a.id = sa.article_id
            WHERE a.is_analyzed = TRUE
            AND a.published_date >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            ORDER BY a.published_date DESC
        """)
        
        result = conn.execute(query)
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
        
        return {
            'articles': articles,
            'sentiment_scores': sentiment_scores
        }

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
    """Render the main dashboard."""
    return render_template('index.html')

@app.route('/api/strategies')
def get_strategies():
    """Get all registered strategies and their status."""
    return jsonify(strategy_manager.get_all_strategies())

@app.route('/api/recommendations')
def get_recommendations():
    """Get filtered recommendations."""
    min_confidence = float(request.args.get('min_confidence', 0.0))
    timeframe = request.args.get('timeframe')
    strategy_name = request.args.get('strategy_name')
    
    recommendations = strategy_manager.get_recommendations(
        min_confidence=min_confidence,
        timeframe=timeframe,
        strategy_name=strategy_name
    )
    return jsonify(recommendations)

@app.route('/api/run-analysis', methods=['POST'])
async def run_analysis():
    """Run all strategies with the provided data."""
    try:
        data = request.json
        recommendations = await strategy_manager.run_all_strategies(data)
        return jsonify({
            'status': 'success',
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/dashboard-data')
async def get_dashboard_data():
    """Get all data needed for the dashboard."""
    try:
        # Fetch data for strategy analysis
        strategy_data = await fetch_strategy_data()
        
        # Run strategies with the fetched data
        recommendations = await strategy_manager.run_all_strategies(strategy_data)
        
        # Get strategy statuses
        strategies = strategy_manager.get_all_strategies()
        
        # Calculate metrics
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
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/health')
def health():
    return jsonify(status="healthy")

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5008))
    app.run(host='0.0.0.0', port=port)