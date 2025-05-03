from typing import List, Dict, Any
from ..base import BaseStrategy
from ..models.recommendation import TradeRecommendation

class ShortTermVolatileStrategy(BaseStrategy):
    """
    Strategy that looks for high-confidence sentiment signals in recent articles
    to identify potential short-term trading opportunities.
    """
    
    def __init__(self, confidence_threshold: float = 0.8):
        super().__init__(
            name="short_term_volatile",
            description="Identifies high-confidence short-term trading opportunities based on recent sentiment analysis"
        )
        self.confidence_threshold = confidence_threshold
    
    def get_required_data(self) -> List[str]:
        return ['articles', 'sentiment_scores']
    
    async def analyze(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        recommendations = []
        
        # Get recent articles with their sentiment analysis
        articles = data.get('articles', [])
        sentiment_scores = data.get('sentiment_scores', {})
        
        for article in articles:
            article_id = article['id']
            sentiment = sentiment_scores.get(article_id)
            
            if not sentiment:
                continue
            
            # Check if sentiment confidence is high enough
            if sentiment['confidence_score'] >= self.confidence_threshold:
                # Get symbols from the article
                symbols = article.get('validated_symbols', [])
                
                for symbol in symbols:
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
                            'article_title': article['title']
                        },
                        strategy_name=self.name
                    )
                    recommendations.append(recommendation.to_dict())
        
        return recommendations 