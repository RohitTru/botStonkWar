from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from datetime import datetime, timedelta
import os, requests
from collections import defaultdict, deque

class SentimentMomentumStrategy(BaseStrategy):
    _alpaca_cache = {}
    _alpaca_cache_ttl = timedelta(minutes=15)

    def __init__(self, confidence_threshold=0.8, lookback=5, momentum_threshold=0.3):
        super().__init__(
            name="sentiment_momentum",
            description="Tracks change in average sentiment for a ticker. If sentiment is rapidly increasing/decreasing, recommend accordingly."
        )
        self.confidence_threshold = confidence_threshold
        self.lookback = lookback
        self.momentum_threshold = momentum_threshold
        self.alpaca_key = os.getenv('ALPACA_KEY')
        self.alpaca_secret = os.getenv('ALPACA_SECRET')
        self.alpaca_url = 'https://data.alpaca.markets/v2/stocks'

    def fetch_live_price(self, symbol):
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

    def get_required_data(self):
        return ['articles', 'sentiment_scores']

    def analyze(self, data):
        recommendations = []
        articles = data.get('articles', [])
        sentiment_scores = data.get('sentiment_scores', {})
        now = datetime.utcnow()
        symbol_sentiments = defaultdict(lambda: deque(maxlen=self.lookback))
        for article in articles:
            article_id = article['id']
            sentiment = sentiment_scores.get(article_id)
            if not sentiment or sentiment['confidence_score'] < self.confidence_threshold:
                continue
            for symbol in article.get('validated_symbols', []):
                symbol_sentiments[symbol].append(sentiment['sentiment_score'])
        for symbol, scores in symbol_sentiments.items():
            if len(scores) < self.lookback:
                continue
            momentum = scores[-1] - scores[0]
            if abs(momentum) >= self.momentum_threshold:
                action = 'buy' if momentum > 0 else 'sell'
                live_data = self.fetch_live_price(symbol)
                recommendations.append(TradeRecommendation(
                    symbol=symbol,
                    action=action,
                    confidence=1.0,
                    reasoning=f"Sentiment momentum: {momentum:+.2f} over {self.lookback} articles.",
                    timeframe='short_term',
                    metadata={'momentum': momentum, 'live_data': live_data},
                    strategy_name=self.name,
                    created_at=now
                ).to_dict())
        return recommendations 