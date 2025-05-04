from typing import List, Dict, Any
from datetime import datetime

class StrategyManager:
    def __init__(self, logger):
        self.logger = logger
        self.strategies = {}
        self.active_strategies = {}
        self.strategy_errors = {}

    def register_strategy(self, strategy: BaseStrategy, active: bool = True):
        """Register a new strategy."""
        self.logger.info(f"Attempting to register strategy: {strategy.__class__.__name__}")
        
        if not isinstance(strategy, BaseStrategy):
            self.logger.error(f"Strategy must inherit from BaseStrategy: {type(strategy)}")
            raise ValueError(f"Strategy must inherit from BaseStrategy: {type(strategy)}")
            
        if not hasattr(strategy, 'name') or not strategy.name:
            self.logger.error("Strategy must have a name")
            raise ValueError("Strategy must have a name")
            
        self.strategies[strategy.name] = strategy
        self.active_strategies[strategy.name] = active
        self.strategy_errors[strategy.name] = []
        self.logger.info(f"Successfully registered strategy {strategy.name} (active={active})")

    def get_all_strategies(self) -> List[BaseStrategy]:
        """Get all registered strategies."""
        strategy_count = len(self.strategies)
        self.logger.info(f"Getting all strategies (count: {strategy_count})")
        if strategy_count == 0:
            self.logger.warning("No strategies are currently registered")
        return list(self.strategies.values())

    def get_strategy_status(self) -> List[Dict[str, Any]]:
        """Get status of all strategies."""
        self.logger.info("Getting status for all strategies")
        status = []
        for strategy in self.get_all_strategies():
            try:
                self.logger.info(f"Getting status for strategy: {strategy.name}")
                strategy_status = strategy.get_status()
                strategy_status['active'] = self.active_strategies.get(strategy.name, False)
                
                # Add error history
                recent_errors = self.strategy_errors.get(strategy.name, [])
                if recent_errors:
                    self.logger.info(f"Found {len(recent_errors)} recent errors for {strategy.name}")
                    strategy_status['metrics']['errors'] = recent_errors[-1]['error']
                    strategy_status['metrics']['last_error_time'] = recent_errors[-1]['timestamp']
                    strategy_status['metrics']['error_count'] = len(recent_errors)
                
                status.append(strategy_status)
                self.logger.info(f"Successfully got status for {strategy.name}")
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
        self.logger.info(f"Returning status for {len(status)} strategies")
        return status 