from typing import List, Dict, Any
from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation
from collections import defaultdict, deque

class SentimentReversalStrategy(BaseStrategy):
    """
    Flags a reversal if a stock has been mostly bearish for days, but suddenly gets a cluster of high-confidence bullish articles (or vice versa).
    """
    def __init__(self, confidence_threshold: float = 0.8, lookback: int = 10, cluster: int = 2):
        super().__init__(
            name="sentiment_reversal",
            description="Flags a reversal if a stock has been mostly bearish for days, but suddenly gets a cluster of high-confidence bullish articles (or vice versa)."
        )
        self.confidence_threshold = confidence_threshold
        self.lookback = lookback
        self.cluster = cluster

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
                    recommendations.append(TradeRecommendation(
                        symbol=symbol,
                        action='buy',
                        confidence=1.0,
                        reasoning=f"Reversal: {self.lookback - self.cluster} bearish then {self.cluster} bullish articles",
                        timeframe='short_term',
                        metadata={'reversal_type': 'bearish_to_bullish'},
                        strategy_name=self.name
                    ).to_dict())
                elif history.count('bullish') >= self.lookback - self.cluster and list(history)[-self.cluster:] == ['bearish'] * self.cluster:
                    recommendations.append(TradeRecommendation(
                        symbol=symbol,
                        action='sell',
                        confidence=1.0,
                        reasoning=f"Reversal: {self.lookback - self.cluster} bullish then {self.cluster} bearish articles",
                        timeframe='short_term',
                        metadata={'reversal_type': 'bullish_to_bearish'},
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