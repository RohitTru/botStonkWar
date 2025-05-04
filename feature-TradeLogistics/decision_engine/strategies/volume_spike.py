from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from datetime import datetime, timedelta
import os
import requests
import time
from collections import defaultdict
from decision_engine.alpaca_ws_price_service import price_service

class VolumeSpikeSentimentStrategy(BaseStrategy):
    _alpaca_cache = {}
    _alpaca_cache_ttl = timedelta(minutes=15)

    def __init__(self, confidence_threshold=0.8, volume_window=5, spike_factor=2.0):
        super().__init__(
            name="volume_spike_sentiment",
            description="Only recommend if there's a volume spike in the stock at the same time as a sentiment spike."
        )
        self.confidence_threshold = confidence_threshold
        self.volume_window = volume_window
        self.spike_factor = spike_factor
        self.alpaca_key = os.getenv('ALPACA_KEY')
        self.alpaca_secret = os.getenv('ALPACA_SECRET')
        self.alpaca_url = 'https://data.alpaca.markets/v2/stocks'

    def get_required_data(self):
        return ['articles', 'sentiment_scores']

    def fetch_live_price(self, symbol):
        ws_price = price_service.get_price(symbol)
        if ws_price and ws_price.get('price') is not None and ws_price.get('volume') is not None:
            return {**ws_price, 'data_source': 'websocket'}
        price_service.subscribe(symbol)
        ws_price = price_service.get_price(symbol)
        if ws_price and ws_price.get('price') is not None and ws_price.get('volume') is not None:
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
            trade_resp = requests.get(f'{self.alpaca_url}/{symbol}/trades/latest', headers=headers)
            trade = trade_resp.json().get('trade', {}) if trade_resp.status_code == 200 else {}
            real_time_volume = trade.get('s')
            bar_resp = requests.get(f'{self.alpaca_url}/{symbol}/bars?timeframe=1Day&limit={self.volume_window+1}', headers=headers)
            bars = bar_resp.json().get('bars', []) if bar_resp.status_code == 200 else []
            volumes = [b.get('v') for b in bars if b.get('v') is not None]
            last_volume = real_time_volume or (volumes[-1] if volumes else None)
            avg_volume = sum(volumes[:-1]) / self.volume_window if len(volumes) > 1 else None
            data = {
                'last_volume': last_volume,
                'avg_volume': avg_volume,
                'real_time_volume': real_time_volume,
                'last_updated': now.isoformat(),
                'status': 'ok' if last_volume is not None else 'unknown',
                'market_closed': None,
                'note': None
            }
            self._alpaca_cache[symbol] = (data, now)
            return {**data, 'data_source': 'rest_api'}
        except Exception as e:
            print(f"[VolumeSpike] Could not fetch live price for {symbol}: {e}")
            return {
                'last_volume': None,
                'avg_volume': None,
                'real_time_volume': None,
                'last_updated': now.isoformat(),
                'status': f'exception: {e}',
                'market_closed': None,
                'note': None,
                'data_source': 'rest_api'
            }

    def analyze(self, data):
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
                    price_data = self.fetch_live_price(symbol)
                    last_volume = price_data.get('real_time_volume') or price_data.get('last_volume')
                    avg_volume = price_data.get('avg_volume')
                    if last_volume is None or avg_volume is None:
                        continue
                    try:
                        reasoning = f"Volume spike: {last_volume} vs avg {avg_volume:.0f} (factor {self.spike_factor}x)"
                    except Exception:
                        reasoning = f"Volume spike: last_volume or avg_volume N/A"
                    if last_volume > self.spike_factor * avg_volume:
                        recommendation = TradeRecommendation(
                            symbol=symbol,
                            action='buy' if sentiment['prediction'] == 'bullish' else 'sell',
                            confidence=sentiment['confidence_score'],
                            reasoning=reasoning,
                            timeframe='short_term',
                            metadata={
                                'last_volume': last_volume,
                                'avg_volume': avg_volume,
                                'real_time_volume': price_data.get('real_time_volume'),
                                'live_data': price_data
                            },
                            strategy_name=self.name,
                            created_at=now
                        )
                        recommendations.append(recommendation.to_dict())
        except Exception as e:
            error = str(e)
            print(f"[VolumeSpike] Error analyzing data: {e}")
        
        # Update metrics after analysis
        self.update_metrics(start_time, recommendations, articles, error)
        return recommendations 