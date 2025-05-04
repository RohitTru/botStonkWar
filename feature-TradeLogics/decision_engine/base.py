from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class BaseStrategy(ABC):
    """Base class for all trading decision strategies."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.last_run = None
        self.metrics = {
            'last_run': None,
            'total_runs': 0,
            'articles_processed': 0,
            'total_articles_processed': 0,
            'recommendations_generated': 0,
            'total_recommendations': 0,
            'high_confidence_articles': 0,
            'total_high_confidence': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'avg_confidence': 0.0,
            'errors': None,
            'last_error_time': None,
            'symbols_analyzed': set(),
            'execution_time_ms': 0,
            'success_rate': 0.0  # Percentage of runs that generated recommendations
        }
    
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze the provided data and generate trading recommendations.
        
        Args:
            data: Dictionary containing all necessary data for analysis
                 (articles, sentiment_scores, price data, etc.)
        
        Returns:
            List of recommendation dictionaries, each containing:
            {
                'symbol': str,
                'action': str,  # 'buy' or 'sell'
                'confidence': float,  # 0.0 to 1.0
                'reasoning': str,
                'timeframe': str,  # 'short_term' or 'long_term'
                'metadata': Dict[str, Any]  # Additional strategy-specific data
            }
        """
        pass
    
    @abstractmethod
    def get_required_data(self) -> List[str]:
        """
        Specify what data this strategy needs to function.
        
        Returns:
            List of required data keys (e.g., ['articles', 'sentiment_scores', 'price_data'])
        """
        pass
    
    def update_metrics(self, start_time: float, recommendations: List[Dict[str, Any]], articles: List[Dict[str, Any]], error: str = None):
        """Update strategy metrics after each run."""
        import time
        
        self.metrics['total_runs'] += 1
        self.metrics['last_run'] = datetime.utcnow()
        self.metrics['execution_time_ms'] = int((time.time() - start_time) * 1000)
        
        # Update article metrics
        articles_count = len(articles) if articles else 0
        self.metrics['articles_processed'] = articles_count
        self.metrics['total_articles_processed'] += articles_count
        
        # Update recommendation metrics
        recs_count = len(recommendations)
        self.metrics['recommendations_generated'] = recs_count
        self.metrics['total_recommendations'] += recs_count
        
        # Calculate buy/sell signals
        buy_signals = len([r for r in recommendations if r['action'] == 'buy'])
        sell_signals = len([r for r in recommendations if r['action'] == 'sell'])
        self.metrics['buy_signals'] = buy_signals
        self.metrics['sell_signals'] = sell_signals
        
        # Calculate average confidence
        if recommendations:
            avg_conf = sum(r['confidence'] for r in recommendations) / len(recommendations)
            self.metrics['avg_confidence'] = round(avg_conf, 2)
        
        # Update symbols analyzed
        symbols = set()
        for rec in recommendations:
            symbols.add(rec['symbol'])
        self.metrics['symbols_analyzed'] = list(symbols)
        
        # Update success rate
        successful_runs = self.metrics['total_runs'] if recs_count > 0 else self.metrics['total_runs'] - 1
        self.metrics['success_rate'] = round((successful_runs / self.metrics['total_runs']) * 100, 2)
        
        # Update error tracking
        if error:
            self.metrics['errors'] = error
            self.metrics['last_error_time'] = datetime.utcnow().isoformat()
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the strategy."""
        return {
            'name': self.name,
            'description': self.description,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'required_data': self.get_required_data(),
            'metrics': self.metrics
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Return the latest metrics for this strategy."""
        return self.metrics 