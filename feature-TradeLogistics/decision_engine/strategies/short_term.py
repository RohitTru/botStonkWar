from typing import List, Dict, Any
from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from datetime import datetime, timedelta
import os
import requests
from decision_engine.alpaca_ws_price_service import price_service

class ShortTermVolatileStrategy(BaseStrategy):
    """
    Strategy that looks for high-confidence sentiment signals in recent articles
    to identify potential short-term trading opportunities.
    """
    
    _alpaca_cache = {}  # symbol -> (data, timestamp)
    _alpaca_cache_ttl = timedelta(minutes=15)

    def __init__(self, confidence_threshold: float = 0.8):
        super().__init__(
            name="short_term_volatile",
            description="Identifies high-confidence short-term trading opportunities based on recent sentiment analysis"
        )
        self.confidence_threshold = confidence_threshold
        self.alpaca_key = os.getenv('ALPACA_KEY')
        self.alpaca_secret = os.getenv('ALPACA_SECRET')
        self.alpaca_url = 'https://data.alpaca.markets/v2/stocks'
    
    def get_required_data(self) -> List[str]:
        return ['articles', 'sentiment_scores']
    
    def fetch_live_price(self, symbol: str) -> Dict[str, Any]:
        # Try WebSocket price service first
        ws_price = price_service.get_price(symbol)
        if ws_price and ws_price.get('price') is not None:
            return ws_price
        # Fallback to REST API/last close as before
        now = datetime.utcnow()
        # Check cache
        cache_entry = self._alpaca_cache.get(symbol)
        if cache_entry:
            data, ts = cache_entry
            if now - ts < self._alpaca_cache_ttl:
                return data
        # Fetch from Alpaca
        try:
            headers = {
                'APCA-API-KEY-ID': self.alpaca_key,
                'APCA-API-SECRET-KEY': self.alpaca_secret
            }
            resp = requests.get(f'{self.alpaca_url}/{symbol}/quotes/latest', headers=headers)
            quote = resp.json().get('quote', {}) if resp.status_code == 200 else {}
            price = quote.get('ap') or quote.get('bp') or quote.get('sp')
            # Fetch last trade for % change and volume
            trade_resp = requests.get(f'{self.alpaca_url}/{symbol}/trades/latest', headers=headers)
            trade = trade_resp.json().get('trade', {}) if trade_resp.status_code == 200 else {}
            last_price = trade.get('p')
            volume = trade.get('s')
            # For % change, fetch previous close
            bar_resp = requests.get(f'{self.alpaca_url}/{symbol}/bars?timeframe=1Day&limit=2', headers=headers)
            bars = bar_resp.json().get('bars', []) if bar_resp.status_code == 200 else []
            change_percent = None
            prev_close = None
            if len(bars) == 2:
                prev_close = bars[0].get('c')
                if last_price and prev_close:
                    change_percent = ((last_price - prev_close) / prev_close) * 100
            # Determine if market is closed (no live price, but we have last close)
            if (last_price is None or last_price == 0) and prev_close:
                data = {
                    'price': prev_close,
                    'change_percent': 0.0,
                    'volume': volume,
                    'last_updated': now.isoformat(),
                    'status': 'market_closed',
                    'market_closed': True,
                    'note': 'Market is closed. Showing last close price.'
                }
                self._alpaca_cache[symbol] = (data, now)
                return data
            # Normal live price
            data = {
                'price': last_price or price or prev_close,
                'change_percent': change_percent,
                'volume': volume,
                'last_updated': now.isoformat(),
                'status': 'ok' if (last_price or price) is not None else 'unknown',
                'market_closed': False,
                'note': None
            }
            self._alpaca_cache[symbol] = (data, now)
            return data
        except Exception as e:
            print(f"[ShortTerm] Could not fetch live price for {symbol}: {e}")
            return {
                'price': None,
                'change_percent': None,
                'volume': None,
                'last_updated': now.isoformat(),
                'status': f'exception: {e}',
                'market_closed': None,
                'note': None
            }
    
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