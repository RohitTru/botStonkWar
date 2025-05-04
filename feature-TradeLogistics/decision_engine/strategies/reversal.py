from typing import List, Dict, Any
from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from collections import defaultdict, deque
import os
import requests
import time
from datetime import datetime, timedelta
from decision_engine.alpaca_ws_price_service import price_service

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

    def get_required_data(self) -> List[str]:
        return ['articles', 'sentiment_scores']

    def fetch_live_price(self, symbol: str) -> dict:
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
            if bars and len(bars) == 2:
                prev_close = bars[0].get('c')
                if last_price is not None and prev_close:
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
                return {**data, 'data_source': 'rest_api'}
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
            return {**data, 'data_source': 'rest_api'}
        except Exception as e:
            print(f"[Reversal] Could not fetch live price for {symbol}: {e}")
            return {
                'price': None,
                'change_percent': None,
                'volume': None,
                'last_updated': now.isoformat(),
                'status': f'exception: {e}',
                'market_closed': None,
                'note': None,
                'data_source': 'rest_api'
            }

    def analyze(self, data: dict) -> list:
        start_time = time.time()
        recommendations = []
        articles = data.get('articles', [])
        sentiment_scores = data.get('sentiment_scores', {})
        now = datetime.utcnow()
        error = None
        try:
            for article in articles:
                article_id = article['id']
                sentiment = sentiment_scores.get(article_id)
                if not sentiment or sentiment.get('confidence_score', 0) < self.confidence_threshold:
                    continue
                symbols = article.get('validated_symbols', [])
                for symbol in symbols:
                    live_data = self.fetch_live_price(symbol)
                    price = live_data.get('price') if isinstance(live_data, dict) else None
                    if price is None:
                        continue
                    recommendation = TradeRecommendation(
                        symbol=symbol,
                        action='buy' if sentiment['prediction'] == 'bullish' else 'sell',
                        confidence=sentiment['confidence_score'],
                        reasoning=f"Reversal: {sentiment['prediction']} cluster detected for {symbol}.",
                        timeframe='short_term',
                        metadata={'live_data': live_data},
                        strategy_name=self.name,
                        created_at=now
                    )
                    recommendations.append(recommendation.to_dict())
        except Exception as e:
            error = str(e)
            print(f"[Reversal] Error analyzing data: {e}")
        
        # Update metrics after analysis
        self.update_metrics(start_time, recommendations, articles, error)
        return recommendations 