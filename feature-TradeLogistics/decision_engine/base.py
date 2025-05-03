from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime

class BaseStrategy(ABC):
    """Base class for all trading decision strategies."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.last_run = None
    
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
    
    def update_last_run(self):
        """Update the timestamp of the last strategy run."""
        self.last_run = datetime.utcnow()
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the strategy."""
        return {
            'name': self.name,
            'description': self.description,
            'last_run': self.last_run,
            'required_data': self.get_required_data()
        } 