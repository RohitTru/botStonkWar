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
        self.strategy_errors: Dict[str, List[Dict[str, Any]]] = {}
    
    def register_strategy(self, strategy: BaseStrategy, active: bool = True):
        """Register a new strategy."""
        if not isinstance(strategy, BaseStrategy):
            raise ValueError(f"Strategy must inherit from BaseStrategy: {type(strategy)}")
            
        if not hasattr(strategy, 'name') or not strategy.name:
            raise ValueError("Strategy must have a name")
            
        self.strategies[strategy.name] = strategy
        self.active_strategies[strategy.name] = active
        self.strategy_errors[strategy.name] = []
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
        if name not in self.strategies:
            raise ValueError(f"Strategy not found: {name}")
            
        self.active_strategies[name] = active
        try:
            self.trade_db.set_strategy_activation(name, active)
            self.logger.info(f"Set strategy {name} active={active}")
        except Exception as e:
            self.logger.error(f"Error setting strategy activation in DB: {e}")
            raise
    
    def _record_strategy_error(self, strategy_name: str, error: Exception):
        """Record an error for a strategy."""
        error_info = {
            'error': str(error),
            'timestamp': datetime.utcnow().isoformat(),
            'type': type(error).__name__
        }
        self.strategy_errors[strategy_name].append(error_info)
        # Keep only last 10 errors
        self.strategy_errors[strategy_name] = self.strategy_errors[strategy_name][-10:]
    
    def run_strategy(self, strategy: BaseStrategy, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run a single strategy."""
        if not isinstance(data, dict):
            raise ValueError(f"Data must be a dictionary, got {type(data)}")
            
        try:
            recommendations = strategy.analyze(data)
            if recommendations:
                self.logger.info(f"Strategy {strategy.name} generated {len(recommendations)} recommendations")
            return recommendations
        except Exception as e:
            self.logger.error(f"Error running strategy {strategy.name}: {e}", exc_info=True)
            self._record_strategy_error(strategy.name, e)
            return []
    
    def run_all_strategies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run all active strategies."""
        if not isinstance(data, dict):
            raise ValueError(f"Data must be a dictionary, got {type(data)}")
            
        all_recommendations = []
        active_strategies = self.get_active_strategies()
        self.logger.info(f"Running {len(active_strategies)} active strategies")
        
        for strategy in active_strategies:
            try:
                recommendations = self.run_strategy(strategy, data)
                all_recommendations.extend(recommendations)
            except Exception as e:
                self.logger.error(f"Error running strategy {strategy.name}: {e}", exc_info=True)
                self._record_strategy_error(strategy.name, e)
                
        return all_recommendations
    
    def get_strategy_status(self) -> List[Dict[str, Any]]:
        """Get status of all strategies."""
        status = []
        for strategy in self.get_all_strategies():
            try:
                strategy_status = strategy.get_status()
                strategy_status['active'] = self.active_strategies.get(strategy.name, False)
                
                # Add error history
                recent_errors = self.strategy_errors.get(strategy.name, [])
                if recent_errors:
                    strategy_status['metrics']['errors'] = recent_errors[-1]['error']
                    strategy_status['metrics']['last_error_time'] = recent_errors[-1]['timestamp']
                    strategy_status['metrics']['error_count'] = len(recent_errors)
                
                status.append(strategy_status)
            except Exception as e:
                self.logger.error(f"Error getting status for strategy {strategy.name}: {e}", exc_info=True)
                self._record_strategy_error(strategy.name, e)
                
                status.append({
                    'name': strategy.name,
                    'description': getattr(strategy, 'description', 'Unknown'),
                    'active': self.active_strategies.get(strategy.name, False),
                    'last_run': None,
                    'metrics': {
                        'health': 'Error',
                        'errors': str(e),
                        'last_error_time': datetime.utcnow().isoformat(),
                        'error_count': len(self.strategy_errors.get(strategy.name, [])),
                        'hourly': {
                            'recommendations_generated': 0,
                            'articles_processed': 0,
                            'success_rate': 0.0,
                            'avg_confidence': 0.0
                        }
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