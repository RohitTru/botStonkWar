from typing import List, Dict, Any, Type
from .base import BaseStrategy
from .models.recommendation import TradeRecommendation

class StrategyManager:
    """Manages and coordinates all trading strategies."""
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.recommendations: List[Dict[str, Any]] = []
    
    def register_strategy(self, strategy: BaseStrategy):
        """Register a new strategy with the manager."""
        self.strategies[strategy.name] = strategy
    
    def get_strategy(self, name: str) -> BaseStrategy:
        """Get a strategy by name."""
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """Get status of all registered strategies."""
        return [strategy.get_status() for strategy in self.strategies.values()]
    
    def run_all_strategies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        print("StrategyManager: Running all strategies synchronously.")
        all_recommendations = []
        for strategy in self.strategies.values():
            try:
                recommendations = strategy.analyze(data)
                strategy.update_last_run()
                all_recommendations.extend(recommendations)
            except Exception as e:
                print(f"Error running strategy {strategy.name}: {str(e)}")
        all_recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        self.recommendations = all_recommendations
        print(f"StrategyManager: Total recommendations generated: {len(all_recommendations)}")
        return all_recommendations
    
    def get_recommendations(self, 
                          min_confidence: float = 0.0,
                          timeframe: str = None,
                          strategy_name: str = None) -> List[Dict[str, Any]]:
        """Get filtered recommendations."""
        filtered = self.recommendations
        
        if min_confidence > 0:
            filtered = [r for r in filtered if r['confidence'] >= min_confidence]
        
        if timeframe:
            filtered = [r for r in filtered if r['timeframe'] == timeframe]
        
        if strategy_name:
            filtered = [r for r in filtered if r['strategy_name'] == strategy_name]
        
        return filtered 