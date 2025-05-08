import os
import logging
from datetime import datetime, timedelta
import sqlalchemy as sa
from sqlalchemy.pool import QueuePool
import json
from rq import get_current_job
from .manager import StrategyManager
from .models.trade_mysql import TradeRecommendationMySQL

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tasks.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection with connection pooling
db_url = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}/{os.getenv('MYSQL_DATABASE')}"
engine = sa.create_engine(
    db_url,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    pool_pre_ping=True
)

# Initialize trade recommendations with MySQL
trade_db = TradeRecommendationMySQL(engine)
strategy_manager = StrategyManager(trade_db)

def fetch_strategy_data():
    try:
        # Get current job for status updates
        job = get_current_job()
        if job:
            job.meta['status'] = 'Fetching data'
            job.save_meta()

        # Fetch recent articles and sentiment data
        with engine.connect() as conn:
            # Get articles from last 30 minutes
            articles_query = """
                SELECT a.*, s.sentiment_score, s.confidence
                FROM articles a
                LEFT JOIN sentiment_analysis s ON a.id = s.article_id
                WHERE a.published_at >= NOW() - INTERVAL 30 MINUTE
                ORDER BY a.published_at DESC
            """
            articles = conn.execute(sa.text(articles_query)).fetchall()

            # Get sentiment scores
            sentiment_query = """
                SELECT symbol, AVG(sentiment_score) as avg_sentiment,
                       COUNT(*) as article_count
                FROM sentiment_analysis
                WHERE created_at >= NOW() - INTERVAL 30 MINUTE
                GROUP BY symbol
            """
            sentiment_scores = conn.execute(sa.text(sentiment_query)).fetchall()

        # Format data for strategies
        strategy_data = {
            'articles': [
                {
                    'id': article.id,
                    'title': article.title,
                    'content': article.content,
                    'symbol': article.symbol,
                    'published_at': article.published_at.isoformat(),
                    'sentiment_score': article.sentiment_score,
                    'confidence': article.confidence
                }
                for article in articles
            ],
            'sentiment_scores': [
                {
                    'symbol': score.symbol,
                    'avg_sentiment': float(score.avg_sentiment),
                    'article_count': score.article_count
                }
                for score in sentiment_scores
            ]
        }

        if job:
            job.meta['status'] = 'Data fetched successfully'
            job.save_meta()

        return strategy_data

    except Exception as e:
        logger.error(f"Error fetching strategy data: {str(e)}")
        if job:
            job.meta['status'] = 'Error fetching data'
            job.meta['error'] = str(e)
            job.save_meta()
        return None

def process_strategies():
    try:
        # Get current job for status updates
        job = get_current_job()
        if job:
            job.meta['status'] = 'Starting strategy processing'
            job.save_meta()

        # Fetch data
        strategy_data = fetch_strategy_data()
        if not strategy_data:
            raise Exception("Failed to fetch strategy data")

        # Get active strategies
        active_strategies = strategy_manager.get_active_strategies()
        
        metrics = {
            'total_recommendations': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'last_updated': datetime.now().isoformat()
        }
        
        recommendations = []
        
        # Process each active strategy
        for strategy in active_strategies:
            try:
                if job:
                    job.meta['status'] = f'Processing strategy: {strategy.name}'
                    job.save_meta()

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
                logger.error(f"Error processing strategy {strategy.name}: {str(e)}")
                continue

        # Save recommendations to database
        for rec in recommendations:
            trade_db.add_recommendation(
                symbol=rec['symbol'],
                strategy=rec['strategy'],
                action=rec['signal'],
                confidence=rec['confidence']
            )

        result = {
            'metrics': metrics,
            'recommendations': recommendations
        }

        if job:
            job.meta['status'] = 'Processing completed'
            job.meta['result'] = result
            job.save_meta()

        return result

    except Exception as e:
        logger.error(f"Error processing strategies: {str(e)}")
        if job:
            job.meta['status'] = 'Error processing strategies'
            job.meta['error'] = str(e)
            job.save_meta()
        raise 