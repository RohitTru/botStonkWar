from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from datetime import datetime, timedelta
import os, requests
from collections import defaultdict

class ObscureStockDetectorStrategy(BaseStrategy):
    _alpaca_cache = {}
    _alpaca_cache_ttl = timedelta(minutes=15)

    def __init__(self, confidence_threshold=0.8, rare_threshold=2, recent_window_days=2):
        super().__init__(
            name="obscure_stock_detector",
            description="Flags rarely-mentioned stocks that suddenly get multiple high-confidence articles."
        )
        self.confidence_threshold = confidence_threshold
        self.rare_threshold = rare_threshold
        self.recent_window_days = recent_window_days
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
        symbol_counts = defaultdict(int)
        recent_articles = []
        for article in articles:
            published_date = datetime.fromisoformat(article['published_date']) if article.get('published_date') else None
            if published_date and (now - published_date).days <= self.recent_window_days:
                recent_articles.append(article)
            for symbol in article.get('validated_symbols', []):
                symbol_counts[symbol] += 1
        # Find rare symbols in the full dataset
        rare_symbols = {s for s, c in symbol_counts.items() if c <= self.rare_threshold}
        # Now, in recent articles, flag if a rare symbol gets multiple high-confidence articles
        rare_recent_counts = defaultdict(int)
        for article in recent_articles:
            article_id = article['id']
            sentiment = sentiment_scores.get(article_id)
            if not sentiment or sentiment['confidence_score'] < self.confidence_threshold:
                continue
            for symbol in article.get('validated_symbols', []):
                if symbol in rare_symbols:
                    rare_recent_counts[symbol] += 1
        for symbol, count in rare_recent_counts.items():
            if count >= 2:  # At least 2 high-confidence recent articles
                live_data = self.fetch_live_price(symbol)
                recommendations.append(TradeRecommendation(
                    symbol=symbol,
                    action='buy',
                    confidence=1.0,
                    reasoning=f"Obscure stock {symbol} got {count} high-confidence articles in {self.recent_window_days} days.",
                    timeframe='short_term',
                    metadata={'rare_recent_count': count, 'live_data': live_data},
                    strategy_name=self.name,
                    created_at=now
                ).to_dict())
        return recommendations 