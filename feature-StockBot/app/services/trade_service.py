from app.services.alpaca_service import AlpacaService
from app.database import db
from app.models.trade import TradeExecution
from datetime import datetime

class TradeService:
    def __init__(self):
        self.alpaca = AlpacaService()

    def execute_trade(self, user_id, symbol, qty, side):
        try:
            order = self.alpaca.submit_order(symbol, qty, side)
            execution = TradeExecution(
                notification_id=None,  # To be filled in with actual notification logic
                alpaca_order_id=order.id,
                execution_price=order.filled_avg_price or 0.0,
                execution_time=datetime.utcnow(),
                status=order.status,
                total_amount=qty * (order.filled_avg_price or 0.0),
                total_shares=qty,
                created_at=datetime.utcnow()
            )
            db.session.add(execution)
            db.session.commit()
            return execution
        except Exception as e:
            # Log error here
            print(f"Trade execution failed: {e}")
            return None 