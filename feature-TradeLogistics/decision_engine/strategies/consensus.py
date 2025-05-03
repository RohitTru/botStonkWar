from typing import List, Dict, Any
from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import os
import requests
from decision_engine.alpaca_ws_price_service import price_service

class SentimentConsensusStrategy(BaseStrategy):
    """
    Recommends a trade if multiple high-confidence articles (default 3+) in the last X minutes agree on direction for the same ticker.
    """
    _alpaca_cache = {}  # symbol -> (data, timestamp)
    _alpaca_cache_ttl = timedelta(minutes=15)

    def __init__(self, confidence_threshold: float = 0.8, min_articles: int = 3, window_minutes: int = 30):
        super().__init__(
            name="sentiment_consensus",
            description="Recommends trades only if multiple high-confidence articles agree on direction for the same ticker in a recent time window."
        )
        self.confidence_threshold = confidence_threshold
        self.min_articles = min_articles
        self.window_minutes = window_minutes
        self.alpaca_key = os.getenv('ALPACA_KEY')
        self.alpaca_secret = os.getenv('ALPACA_SECRET')
        self.alpaca_url = 'https://data.alpaca.markets/v2/stocks'

    def fetch_live_price(self, symbol: str) -> Dict[str, Any]:
        ws_price = price_service.get_price(symbol)
        if ws_price and ws_price.get('price') is not None:
            return ws_price
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
        symbol_sentiments = defaultdict(list)
        articles_processed = 0
        high_confidence_articles = 0
        errors = None
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)
        try:
            for article in articles:
                # Only consider articles in the time window
                published_date = datetime.fromisoformat(article['published_date']) if article['published_date'] else None
                if not published_date or published_date < window_start:
                    continue
                article_id = article['id']
                sentiment = sentiment_scores.get(article_id)
                if not sentiment:
                    continue
                if sentiment['confidence_score'] >= self.confidence_threshold:
                    high_confidence_articles += 1
                    direction = sentiment['prediction']
                    for symbol in article.get('validated_symbols', []):
                        symbol_sentiments[symbol].append(direction)
                articles_processed += 1
            # Now, for each symbol, check if enough articles agree
            for symbol, directions in symbol_sentiments.items():
                count = Counter(directions)
                for direction, num in count.items():
                    if num >= self.min_articles:
                        live_data = self.fetch_live_price(symbol)
                        recommendations.append(TradeRecommendation(
                            symbol=symbol,
                            action='buy' if direction == 'bullish' else 'sell',
                            confidence=1.0,  # Consensus, so max confidence
                            reasoning=f"{num} high-confidence articles agree on {direction} for {symbol} in last {self.window_minutes} min",
                            timeframe='short_term',
                            metadata={'consensus_count': num, 'window_minutes': self.window_minutes, 'live_data': live_data},
                            strategy_name=self.name,
                            created_at=now,
                        ).to_dict())
            print(f"[Consensus] Processed {articles_processed} articles, {high_confidence_articles} high-confidence, {len(recommendations)} recommendations.")
        except Exception as e:
            errors = str(e)
            print(f"Error in SentimentConsensusStrategy: {errors}")
        self.metrics['articles_processed'] = articles_processed
        self.metrics['recommendations_generated'] = len(recommendations)
        self.metrics['high_confidence_articles'] = high_confidence_articles
        self.metrics['errors'] = errors
        return recommendations 