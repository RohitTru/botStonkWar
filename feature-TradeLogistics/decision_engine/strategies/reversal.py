from typing import List, Dict, Any
from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from collections import defaultdict, deque
import os
import requests
from datetime import datetime, timedelta

class SentimentReversalStrategy(BaseStrategy):
    """
    Flags a reversal if a stock has been mostly bearish for days, but suddenly gets a cluster of high-confidence bullish articles (or vice versa).
    """
    _alpaca_cache = {}  # symbol -> (data, timestamp)
    _alpaca_cache_ttl = timedelta(minutes=15)

    def __init__(self, confidence_threshold: float = 0.8, lookback: int = 10, cluster: int = 2):
        super().__init__(
            name="sentiment_reversal",
            description="Flags a reversal if a stock has been mostly bearish for days, but suddenly gets a cluster of high-confidence bullish articles (or vice versa)."
        )
        self.confidence_threshold = confidence_threshold
        self.lookback = lookback
        self.cluster = cluster
        self.alpaca_key = os.getenv('ALPACA_KEY')
        self.alpaca_secret = os.getenv('ALPACA_SECRET')
        self.alpaca_url = 'https://data.alpaca.markets/v2/stocks'

    def fetch_live_price(self, symbol: str) -> Dict[str, Any]:
        now = datetime.utcnow()
        cache_entry = self._alpaca_cache.get(symbol)
        if cache_entry:
            data, ts = cache_entry
            if now - ts < self._alpaca_cache_ttl:
                return data
        try:
            headers = {
                'APCA-API-KEY-ID': self.alpaca_key,
                'APCA-API-SECRET-KEY': self.alpaca_secret
            }
            resp = requests.get(f'{self.alpaca_url}/{symbol}/quotes/latest', headers=headers)
            quote = resp.json().get('quote', {}) if resp.status_code == 200 else {}
            price = quote.get('ap') or quote.get('bp') or quote.get('sp')
            trade_resp = requests.get(f'{self.alpaca_url}/{symbol}/trades/latest', headers=headers)
            trade = trade_resp.json().get('trade', {}) if trade_resp.status_code == 200 else {}
            last_price = trade.get('p')
            volume = trade.get('s')
            bar_resp = requests.get(f'{self.alpaca_url}/{symbol}/bars?timeframe=1Day&limit=2', headers=headers)
            bars = bar_resp.json().get('bars', []) if bar_resp.status_code == 200 else []
            change_percent = None
            prev_close = None
            if len(bars) == 2:
                prev_close = bars[0].get('c')
                if last_price and prev_close:
                    change_percent = ((last_price - prev_close) / prev_close) * 100
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
            return {
                'price': None,
                'change_percent': None,
                'volume': None,
                'last_updated': now.isoformat(),
                'status': f'exception: {e}',
                'market_closed': None,
                'note': None
            }

    def get_required_data(self) -> List[str]:
        return ['articles', 'sentiment_scores']

    def analyze(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        recommendations = []
        articles = data.get('articles', [])
        sentiment_scores = data.get('sentiment_scores', {})
        symbol_history = defaultdict(lambda: deque(maxlen=self.lookback))
        articles_processed = 0
        high_confidence_articles = 0
        errors = None
        try:
            # Build sentiment history for each symbol
            for article in articles:
                article_id = article['id']
                sentiment = sentiment_scores.get(article_id)
                if not sentiment:
                    continue
                if sentiment['confidence_score'] >= self.confidence_threshold:
                    high_confidence_articles += 1
                    for symbol in article.get('validated_symbols', []):
                        symbol_history[symbol].append(sentiment['prediction'])
                articles_processed += 1
            # Look for reversals
            for symbol, history in symbol_history.items():
                if len(history) < self.lookback:
                    continue
                # If most of lookback is bearish, but last cluster are bullish (or vice versa)
                if history.count('bearish') >= self.lookback - self.cluster and list(history)[-self.cluster:] == ['bullish'] * self.cluster:
                    live_data = self.fetch_live_price(symbol)
                    recommendations.append(TradeRecommendation(
                        symbol=symbol,
                        action='buy',
                        confidence=1.0,
                        reasoning=f"Reversal: {self.lookback - self.cluster} bearish then {self.cluster} bullish articles",
                        timeframe='short_term',
                        metadata={'reversal_type': 'bearish_to_bullish', 'live_data': live_data},
                        strategy_name=self.name
                    ).to_dict())
                elif history.count('bullish') >= self.lookback - self.cluster and list(history)[-self.cluster:] == ['bearish'] * self.cluster:
                    live_data = self.fetch_live_price(symbol)
                    recommendations.append(TradeRecommendation(
                        symbol=symbol,
                        action='sell',
                        confidence=1.0,
                        reasoning=f"Reversal: {self.lookback - self.cluster} bullish then {self.cluster} bearish articles",
                        timeframe='short_term',
                        metadata={'reversal_type': 'bullish_to_bearish', 'live_data': live_data},
                        strategy_name=self.name
                    ).to_dict())
            print(f"[Reversal] Processed {articles_processed} articles, {high_confidence_articles} high-confidence, {len(recommendations)} recommendations.")
        except Exception as e:
            errors = str(e)
            print(f"Error in SentimentReversalStrategy: {errors}")
        self.metrics['articles_processed'] = articles_processed
        self.metrics['recommendations_generated'] = len(recommendations)
        self.metrics['high_confidence_articles'] = high_confidence_articles
        self.metrics['errors'] = errors
        return recommendations 