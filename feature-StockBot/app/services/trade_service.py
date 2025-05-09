from app.services.alpaca_service import AlpacaService
from app.database import db
from app.models.trade import TradeExecution, TradeRecommendation, TradeAcceptance, TradeExecutionLog
from datetime import datetime
from sqlalchemy import and_

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

    def expire_recommendations(self):
        now = datetime.utcnow()
        expired = TradeRecommendation.query.filter(
            and_(TradeRecommendation.expires_at < now, TradeRecommendation.status == 'PENDING')
        ).all()
        for rec in expired:
            rec.status = 'EXPIRED'
            db.session.add(rec)
        db.session.commit()
        return len(expired)

    def execute_eligible_recommendations(self):
        now = datetime.utcnow()
        eligible = TradeRecommendation.query.filter(
            and_(TradeRecommendation.status == 'PENDING', TradeRecommendation.expires_at <= now)
        ).all()
        executed_count = 0
        for rec in eligible:
            acceptances = TradeAcceptance.query.filter_by(trade_recommendation_id=rec.id, status='ACCEPTED').all()
            total_allocation_amount = sum(float(a.allocation_amount or 0) for a in acceptances)
            total_allocation_shares = sum(float(a.allocation_shares or 0) for a in acceptances)
            # Use shares if available, else fallback to rec.shares
            order_qty = total_allocation_shares if total_allocation_shares > 0 else float(rec.shares)
            try:
                if order_qty > 0:
                    order = self.alpaca.submit_order(rec.symbol, order_qty, rec.action.lower())
                    execution = TradeExecution(
                        notification_id=None,
                        alpaca_order_id=order.id,
                        execution_price=order.filled_avg_price or 0.0,
                        execution_time=datetime.utcnow(),
                        status=order.status,
                        total_amount=total_allocation_amount if total_allocation_amount > 0 else float(rec.amount),
                        total_shares=order_qty,
                        created_at=datetime.utcnow()
                    )
                    db.session.add(execution)
                    rec.status = 'EXECUTED'
                    db.session.add(rec)
                    log = TradeExecutionLog(
                        trade_recommendation_id=rec.id,
                        executed_at=datetime.utcnow(),
                        status='SUCCESS',
                        details=f"Order ID: {order.id}, Allocated Amount: {total_allocation_amount}, Allocated Shares: {order_qty}"
                    )
                    db.session.add(log)
                    executed_count += 1
                else:
                    log = TradeExecutionLog(
                        trade_recommendation_id=rec.id,
                        executed_at=datetime.utcnow(),
                        status='FAILED',
                        details='No allocation from users.'
                    )
                    db.session.add(log)
            except Exception as e:
                log = TradeExecutionLog(
                    trade_recommendation_id=rec.id,
                    executed_at=datetime.utcnow(),
                    status='FAILED',
                    details=str(e)
                )
                db.session.add(log)
        db.session.commit()
        return executed_count

    def get_active_recommendations(self):
        now = datetime.utcnow()
        return TradeRecommendation.query.filter(
            and_(TradeRecommendation.status == 'PENDING', TradeRecommendation.expires_at > now)
        ).all()

    def get_expired_recommendations(self):
        now = datetime.utcnow()
        return TradeRecommendation.query.filter(
            and_(TradeRecommendation.status == 'EXPIRED', TradeRecommendation.expires_at < now)
        ).all()

    def create_recommendation(self, symbol, action, amount, shares, timeframe, expires_at, required_acceptances=1):
        rec = TradeRecommendation(
            symbol=symbol,
            action=action,
            amount=amount,
            shares=shares,
            timeframe=timeframe,
            expires_at=expires_at,
            required_acceptances=required_acceptances,
            status='PENDING',
        )
        db.session.add(rec)
        db.session.commit()
        return rec

    def process_expiry_and_execution(self):
        expired = self.expire_recommendations()
        executed = self.execute_eligible_recommendations()
        return {'expired': expired, 'executed': executed} 