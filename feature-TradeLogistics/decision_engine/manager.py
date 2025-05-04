from typing import List, Dict, Any, Type
import time
from .base import BaseStrategy
from .models.recommendation import TradeRecommendation
from datetime import datetime
import logging

class StrategyManager:
    """Manages the lifecycle and execution of trading strategies."""
    
    def __init__(self, trade_db):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.active_strategies: Dict[str, bool] = {}
        self.trade_db = trade_db
        self.logger = logging.getLogger(__name__)
    
    def register_strategy(self, strategy: BaseStrategy, active: bool = True):
        """Register a new strategy."""
        self.strategies[strategy.name] = strategy
        self.active_strategies[strategy.name] = active
        self.logger.info(f"Registered strategy {strategy.name} (active={active})")
    
    def get_strategy(self, name: str) -> BaseStrategy:
        """Get a strategy by name."""
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> List[BaseStrategy]:
        """Get all registered strategies."""
        return list(self.strategies.values())
    
    def get_active_strategies(self) -> List[BaseStrategy]:
        """Get all active strategies."""
        return [s for name, s in self.strategies.items() if self.active_strategies.get(name, False)]
    
    def set_strategy_active(self, name: str, active: bool):
        """Set whether a strategy is active."""
        if name in self.strategies:
            self.active_strategies[name] = active
            self.trade_db.set_strategy_activation(name, active)
            self.logger.info(f"Set strategy {name} active={active}")
    
    def run_strategy(self, strategy: BaseStrategy, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run a single strategy."""
        try:
            recommendations = strategy.analyze(data)
            return recommendations
        except Exception as e:
            self.logger.error(f"Error running strategy {strategy.name}: {e}")
            return []
    
    def run_all_strategies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run all active strategies."""
        all_recommendations = []
        for strategy in self.get_active_strategies():
            try:
                recommendations = self.run_strategy(strategy, data)
                all_recommendations.extend(recommendations)
            except Exception as e:
                self.logger.error(f"Error running strategy {strategy.name}: {e}")
        return all_recommendations
    
    def get_strategy_status(self) -> List[Dict[str, Any]]:
        """Get status of all strategies."""
        status = []
        for strategy in self.get_all_strategies():
            try:
                strategy_status = strategy.get_status()
                strategy_status['active'] = self.active_strategies.get(strategy.name, False)
                status.append(strategy_status)
            except Exception as e:
                self.logger.error(f"Error getting status for strategy {strategy.name}: {e}")
                status.append({
                    'name': strategy.name,
                    'description': getattr(strategy, 'description', 'Unknown'),
                    'active': self.active_strategies.get(strategy.name, False),
                    'last_run': None,
                    'metrics': {
                        'health': 'Error',
                        'errors': f"Error getting status: {e}",
                        'last_error_time': datetime.utcnow().isoformat()
                    }
                })
        return status
    
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