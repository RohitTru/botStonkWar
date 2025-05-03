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

# Database connection using Docker environment variables
DB_USER = os.getenv('MYSQL_USER')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD')
DB_HOST = os.getenv('MYSQL_HOST')
DB_NAME = os.getenv('MYSQL_DATABASE')

app.logger.info(f'Connecting to database at {DB_HOST}')

engine = create_engine(f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}')
Session = sessionmaker(bind=engine)

# Register strategies
strategy_manager.register_strategy(ShortTermVolatileStrategy(confidence_threshold=0.8))

def fetch_strategy_data():
    with engine.connect() as conn:
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
            ORDER BY sa.analysis_timestamp DESC
            LIMIT 30
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
        print(f"Fetched {len(articles)} articles from DB for strategy analysis.")
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
    # Always fetch and run strategies before returning recommendations
    strategy_data = fetch_strategy_data()
    strategy_manager.run_all_strategies(strategy_data)
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

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5008))
    app.run(host='0.0.0.0', port=port)