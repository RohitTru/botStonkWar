from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from datetime import datetime, timedelta
import os, requests
from decision_engine.alpaca_ws_price_service import price_service

class SentimentDivergenceStrategy(BaseStrategy):
    _alpaca_cache = {}
    _alpaca_cache_ttl = timedelta(minutes=15)

    def __init__(self, confidence_threshold=0.8):
        super().__init__(
            name="sentiment_divergence",
            description="Flag if sentiment is bullish but price is falling (or vice versa)."
        )
        self.confidence_threshold = confidence_threshold
        self.alpaca_key = os.getenv('ALPACA_KEY')
        self.alpaca_secret = os.getenv('ALPACA_SECRET')
        self.alpaca_url = 'https://data.alpaca.markets/v2/stocks'

    def fetch_live_price(self, symbol):
        ws_price = price_service.get_price(symbol)
        if ws_price and ws_price.get('price') is not None:
            return {**ws_price, 'data_source': 'websocket'}
        price_service.subscribe(symbol)
        ws_price = price_service.get_price(symbol)
        if ws_price and ws_price.get('price') is not None:
            return {**ws_price, 'data_source': 'websocket'}
        now = datetime.utcnow()
        cache_entry = self._alpaca_cache.get(symbol)
        if cache_entry:
            data, ts = cache_entry
            if now - ts < self._alpaca_cache_ttl:
                return {**data, 'data_source': 'rest_api'}
        try:
            headers = {
                'APCA-API-KEY-ID': self.alpaca_key,
                'APCA-API-SECRET-KEY': self.alpaca_secret
            }
            bar_resp = requests.get(f'{self.alpaca_url}/{symbol}/bars?timeframe=1Day&limit=2', headers=headers)
            bars = bar_resp.json().get('bars', []) if bar_resp.status_code == 200 else []
            last_close = bars[-1].get('c') if bars and len(bars) == 2 else None
            prev_close = bars[0].get('c') if bars and len(bars) == 2 else None
            change_percent = None
            if last_close is not None and prev_close:
                change_percent = ((last_close - prev_close) / prev_close) * 100
            data = {
                'price': last_close,
                'change_percent': change_percent,
                'last_updated': now.isoformat(),
                'status': 'ok' if last_close is not None else 'unknown',
                'market_closed': None,
                'note': None
            }
            self._alpaca_cache[symbol] = (data, now)
            return {**data, 'data_source': 'rest_api'}
        except Exception as e:
            print(f"[SentimentDivergence] Could not fetch live price for {symbol}: {e}")
            return {
                'price': None,
                'change_percent': None,
                'last_updated': now.isoformat(),
                'status': f'exception: {e}',
                'market_closed': None,
                'note': None,
                'data_source': 'rest_api'
            }

    def get_required_data(self):
        return ['articles', 'sentiment_scores']

    def analyze(self, data):
        recommendations = []
        articles = data.get('articles', [])
        sentiment_scores = data.get('sentiment_scores', {})
        now = datetime.utcnow()
        for article in articles:
            article_id = article['id']
            sentiment = sentiment_scores.get(article_id)
            if not sentiment or sentiment.get('confidence_score', 0) < self.confidence_threshold:
                continue
            symbols = article.get('validated_symbols', [])
            for symbol in symbols:
                price_data = self.fetch_live_price(symbol)
                price = price_data.get('price') if isinstance(price_data, dict) else None
                if price is None:
                    continue
                recommendation = TradeRecommendation(
                    symbol=symbol,
                    action='buy' if sentiment['prediction'] == 'bullish' else 'sell',
                    confidence=sentiment['confidence_score'],
                    reasoning=f"Divergence: {sentiment['prediction']} sentiment but price action diverges for {symbol}.",
                    timeframe='short_term',
                    metadata={'live_data': price_data},
                    strategy_name=self.name,
                    created_at=now
                )
                recommendations.append(recommendation.to_dict())
        return recommendations 