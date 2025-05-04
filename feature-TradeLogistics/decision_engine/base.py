from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime, timedelta
import time

class BaseStrategy(ABC):
    """Base class for all trading decision strategies."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.last_run = None
        self._reset_hourly_metrics()
        self.metrics = {
            'last_run': None,
            'total_runs': 0,
            'total_articles_processed': 0,
            'total_recommendations': 0,
            'total_buy_signals': 0,
            'total_sell_signals': 0,
            'all_time_success_rate': 0.0,
            'health': 'Unknown',
            'errors': None,
            'last_error_time': None,
            # Hourly metrics
            'hourly': {
                'start_time': None,
                'recommendations_generated': 0,
                'articles_processed': 0,
                'buy_signals': 0,
                'sell_signals': 0,
                'success_rate': 0.0,
                'avg_confidence': 0.0,
                'avg_buy_confidence': 0.0,
                'avg_sell_confidence': 0.0,
                'execution_time_ms': 0
            }
        }
    
    def _reset_hourly_metrics(self):
        """Reset hourly metrics when they expire."""
        self.metrics['hourly'] = {
            'start_time': datetime.utcnow().isoformat(),
            'recommendations_generated': 0,
            'articles_processed': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'success_rate': 0.0,
            'avg_confidence': 0.0,
            'avg_buy_confidence': 0.0,
            'avg_sell_confidence': 0.0,
            'execution_time_ms': 0
        }
    
    def _check_hourly_metrics(self):
        """Check if hourly metrics need to be reset."""
        if not self.metrics['hourly']['start_time']:
            self._reset_hourly_metrics()
            return
        
        start_time = datetime.fromisoformat(self.metrics['hourly']['start_time'])
        if datetime.utcnow() - start_time > timedelta(hours=1):
            self._reset_hourly_metrics()
    
    @abstractmethod
    async def analyze(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze the provided data and generate trading recommendations.
        
        Args:
            data: Dictionary containing all necessary data for analysis
                 (articles, sentiment scores, price data, etc.)
        
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
        self._check_hourly_metrics()
        
        # Update run statistics
        self.metrics['total_runs'] += 1
        self.metrics['last_run'] = datetime.utcnow().isoformat()
        execution_time = int((time.time() - start_time) * 1000)
        
        # Update article metrics
        articles_count = len(articles) if articles else 0
        self.metrics['total_articles_processed'] += articles_count
        self.metrics['hourly']['articles_processed'] += articles_count
        
        # Update recommendation metrics
        recs_count = len(recommendations)
        self.metrics['total_recommendations'] += recs_count
        self.metrics['hourly']['recommendations_generated'] += recs_count
        
        # Calculate buy/sell signals
        buy_signals = len([r for r in recommendations if r['action'] == 'buy'])
        sell_signals = len([r for r in recommendations if r['action'] == 'sell'])
        
        self.metrics['total_buy_signals'] += buy_signals
        self.metrics['total_sell_signals'] += sell_signals
        self.metrics['hourly']['buy_signals'] += buy_signals
        self.metrics['hourly']['sell_signals'] += sell_signals
        
        # Calculate confidence metrics
        if recommendations:
            all_conf = [r['confidence'] for r in recommendations]
            buy_conf = [r['confidence'] for r in recommendations if r['action'] == 'buy']
            sell_conf = [r['confidence'] for r in recommendations if r['action'] == 'sell']
            
            self.metrics['hourly']['avg_confidence'] = round(sum(all_conf) / len(all_conf), 2)
            if buy_conf:
                self.metrics['hourly']['avg_buy_confidence'] = round(sum(buy_conf) / len(buy_conf), 2)
            if sell_conf:
                self.metrics['hourly']['avg_sell_confidence'] = round(sum(sell_conf) / len(sell_conf), 2)
        
        # Update success rates
        hourly_success = recs_count > 0
        total_success = self.metrics['total_recommendations'] > 0
        
        self.metrics['hourly']['success_rate'] = round((hourly_success / self.metrics['total_runs']) * 100, 2)
        self.metrics['all_time_success_rate'] = round((total_success / self.metrics['total_runs']) * 100, 2)
        
        # Update execution time
        self.metrics['hourly']['execution_time_ms'] = execution_time
        
        # Update health status
        if error:
            self.metrics['health'] = 'Error'
            self.metrics['errors'] = error
            self.metrics['last_error_time'] = datetime.utcnow().isoformat()
        elif recs_count > 0 or articles_count > 0:
            self.metrics['health'] = 'Healthy'
        else:
            self.metrics['health'] = 'Idle'
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the strategy."""
        self._check_hourly_metrics()  # Ensure hourly metrics are current
        return {
            'name': self.name,
            'description': self.description,
            'last_run': self.metrics['last_run'],
            'required_data': self.get_required_data(),
            'metrics': self.metrics
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Return the latest metrics for this strategy."""
        return self.metrics 