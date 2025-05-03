from typing import List, Dict, Any
from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from datetime import datetime
import importlib

class ShortTermVolatileStrategy(BaseStrategy):
    """
    Strategy that looks for high-confidence sentiment signals in recent articles
    to identify potential short-term trading opportunities.
    """
    
    def __init__(self, confidence_threshold: float = 0.8):
        super().__init__(
            name="short_term_volatile",
            description="Identifies high-confidence short-term trading opportunities based on recent sentiment analysis"
        )
        self.confidence_threshold = confidence_threshold
    
    def get_required_data(self) -> List[str]:
        return ['articles', 'sentiment_scores']
    
    def fetch_live_price(self, symbol: str) -> Dict[str, Any]:
        try:
            yf = importlib.import_module('yfinance')
            ticker = yf.Ticker(symbol)
            info = ticker.info
            price = info.get('regularMarketPrice')
            change = info.get('regularMarketChangePercent')
            volume = info.get('regularMarketVolume')
            return {
                'price': price,
                'change_percent': change,
                'volume': volume
            }
        except Exception as e:
            print(f"[ShortTerm] Could not fetch live price for {symbol}: {e}")
            return {}
    
    def analyze(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        recommendations = []
        articles_processed = 0
        high_confidence_articles = 0
        errors = None
        now = datetime.utcnow()
        try:
            # Get recent articles with their sentiment analysis
            articles = data.get('articles', [])
            sentiment_scores = data.get('sentiment_scores', {})
            articles_processed = len(articles)
            print(f"Analyzing {len(articles)} articles in strategy.")
            print(f"Sentiment scores keys: {list(sentiment_scores.keys())}")
            
            for article in articles:
                article_id = article['id']
                sentiment = sentiment_scores.get(article_id)
                if not sentiment:
                    print(f"No sentiment for article {article_id}")
                    continue
                # Check if sentiment confidence is high enough
                if sentiment['confidence_score'] >= self.confidence_threshold:
                    print(f"High confidence article: {article_id}, score: {sentiment['confidence_score']}")
                    high_confidence_articles += 1
                    # Get symbols from the article
                    symbols = article.get('validated_symbols', [])
                    print(f"Symbols for article {article_id}: {symbols}")
                    for symbol in symbols:
                        live_data = self.fetch_live_price(symbol)
                        recommendation = TradeRecommendation(
                            symbol=symbol,
                            action='buy' if sentiment['prediction'] == 'bullish' else 'sell',
                            confidence=sentiment['confidence_score'],
                            reasoning=f"High confidence {sentiment['prediction']} signal from recent article",
                            timeframe='short_term',
                            metadata={
                                'article_id': article_id,
                                'sentiment_score': sentiment['sentiment_score'],
                                'confidence_score': sentiment['confidence_score'],
                                'article_title': article['title'],
                                'live_data': live_data
                            },
                            strategy_name=self.name,
                            created_at=now,
                            trade_time=now
                        )
                        recommendations.append(recommendation.to_dict())
            print(f"Generated {len(recommendations)} recommendations.")
        except Exception as e:
            errors = str(e)
            print(f"Error in strategy analyze: {errors}")
        
        # Update metrics
        self.metrics['articles_processed'] = articles_processed
        self.metrics['recommendations_generated'] = len(recommendations)
        self.metrics['high_confidence_articles'] = high_confidence_articles
        self.metrics['errors'] = errors
        
        return recommendations 