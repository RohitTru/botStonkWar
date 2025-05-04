import time
import logging
from typing import List, Dict, Any
from .base import BaseStrategy

class StrategyManager:
    def __init__(self, trade_db):
        self.strategies = {}
        self.trade_db = trade_db
        self.logger = logging.getLogger(__name__)

    def register_strategy(self, strategy: BaseStrategy, active: bool = True) -> None:
        """Register a new strategy."""
        self.strategies[strategy.name] = {
            'strategy': strategy,
            'active': active
        }
    
    def get_active(self, name: str) -> bool:
        """Get the active status of a strategy."""
        return self.strategies.get(name, {}).get('active', False)
    
    def set_active(self, name: str, active: bool) -> None:
        """Set the active status of a strategy."""
        if name in self.strategies:
            self.strategies[name]['active'] = active
            self.trade_db.set_strategy_activation(name, active)
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """Get status of all strategies."""
        return [
            {**strat['strategy'].get_status(), 'active': strat['active']}
            for strat in self.strategies.values()
        ]

    async def run_all_strategies(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run all active strategies and collect their recommendations."""
        self.logger.info("Running all strategies synchronously.")
        all_recommendations = []
        
        for strat_name, strat_info in self.strategies.items():
            if not strat_info['active']:
                continue
                
            strategy = strat_info['strategy']
            start_time = time.time()
            
            try:
                recommendations = await strategy.analyze(data)
                strategy.update_metrics(
                    start_time=start_time,
                    recommendations=recommendations,
                    articles=data.get('articles', [])
                )
                
                # Add strategy name to recommendations
                for rec in recommendations:
                    rec['strategy_name'] = strat_name
                
                all_recommendations.extend(recommendations)
                
            except Exception as e:
                error_msg = f"Error running strategy {strat_name}: {str(e)}"
                self.logger.error(error_msg)
                strategy.update_metrics(
                    start_time=start_time,
                    recommendations=[],
                    articles=data.get('articles', []),
                    error=error_msg
                )
        
        self.logger.info(f"Total recommendations generated: {len(all_recommendations)}")
        return all_recommendations 