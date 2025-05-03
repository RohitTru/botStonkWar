from typing import List, Dict, Any
from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from collections import defaultdict, Counter
from datetime import datetime, timedelta

class SentimentConsensusStrategy(BaseStrategy):
    """
    Recommends a trade if multiple high-confidence articles (default 3+) in the last X minutes agree on direction for the same ticker.
    """
    def __init__(self, confidence_threshold: float = 0.8, min_articles: int = 3, window_minutes: int = 30):
        super().__init__(
            name="sentiment_consensus",
            description="Recommends trades only if multiple high-confidence articles agree on direction for the same ticker in a recent time window."
        )
        self.confidence_threshold = confidence_threshold
        self.min_articles = min_articles
        self.window_minutes = window_minutes

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
                        recommendations.append(TradeRecommendation(
                            symbol=symbol,
                            action='buy' if direction == 'bullish' else 'sell',
                            confidence=1.0,  # Consensus, so max confidence
                            reasoning=f"{num} high-confidence articles agree on {direction} for {symbol} in last {self.window_minutes} min",
                            timeframe='short_term',
                            metadata={'consensus_count': num, 'window_minutes': self.window_minutes},
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