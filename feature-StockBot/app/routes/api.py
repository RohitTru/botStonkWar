from flask import Blueprint, request, jsonify
from app.services.trade_service import TradeService
from app.services.alpaca_service import AlpacaService
from app.models.user import User
from app.database import db
from sqlalchemy.exc import NoResultFound
from datetime import datetime, timedelta
from app.models.trade import TradeAcceptance, TradeExecutionLog, TradeRecommendation
from sqlalchemy import desc, text

api_bp = Blueprint('api', __name__)
trade_service = TradeService()

@api_bp.route('/trade', methods=['POST'])
def execute_trade():
    data = request.json
    user_id = data.get('user_id')
    symbol = data.get('symbol')
    qty = data.get('qty')
    side = data.get('side')
    result = trade_service.execute_trade(user_id, symbol, qty, side)
    if result:
        return jsonify({'status': 'success', 'trade': {
            'order_id': result.alpaca_order_id,
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'status': result.status
        }}), 200
    else:
        return jsonify({'status': 'error', 'message': 'Trade execution failed'}), 500

@api_bp.route('/metrics', methods=['GET'])
def get_metrics():
    try:
        # Simple count query that doesn't include columns
        user_count = db.session.query(db.func.count(User.id)).scalar()
        
        # Fetch live balance from Alpaca with error handling
        try:
            alpaca = AlpacaService()
            account = alpaca.api.get_account()
            portfolio_value = float(account.portfolio_value)
            pnl = float(account.equity) - float(account.last_equity)
        except Exception as e:
            print(f"Error fetching Alpaca data: {e}")
            portfolio_value = 0.0
            pnl = 0.0
            
        metrics = {
            'portfolio_value': portfolio_value,
            'pnl': pnl,
            'active_users': user_count
        }
        return jsonify(metrics)
    except Exception as e:
        print(f"Error in metrics endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/brokerage/add_funds', methods=['POST'])
def add_funds():
    data = request.json
    amount = float(data.get('amount', 0))
    # This is a simulation; does not affect Alpaca
    return jsonify({'status': 'success', 'added': amount, 'new_balance': 'live from Alpaca'})

@api_bp.route('/users', methods=['GET'])
def get_users():
    # Optionally support search
    search = request.args.get('search', '').strip()
    query = db.session.query(User)
    if search:
        query = query.filter(User.username.ilike(f'%{search}%'))
    users = query.order_by(User.balance.desc()).all()
    # Placeholder equity and P&L
    user_list = [
        {
            'username': u.username,
            'equity': float(u.balance),
            'pnl': 0.0,  # Placeholder
        } for u in users
    ]
    return jsonify(user_list)

@api_bp.route('/trades', methods=['GET'])
def get_trades():
    # Placeholder data; replace with real trade data later
    trades = [
        {
            'symbol': 'AAPL',
            'type': 'BUY',
            'status': 'EXECUTED',
            'users': 5,
            'details': 'Bought 10 shares at $150',
        },
        {
            'symbol': 'TSLA',
            'type': 'SELL',
            'status': 'PENDING',
            'users': 3,
            'details': 'Sell order for 5 shares',
        },
    ]
    return jsonify(trades)

@api_bp.route('/orders', methods=['GET'])
def get_orders():
    alpaca = AlpacaService()
    orders = alpaca.api.list_orders(status='all', limit=50)
    order_list = [
        {
            'symbol': o.symbol,
            'qty': o.qty,
            'side': o.side,
            'status': o.status,
            'filled_avg_price': o.filled_avg_price,
            'submitted_at': o.submitted_at.isoformat() if o.submitted_at else '',
        } for o in orders
    ]
    return jsonify(order_list)

@api_bp.route('/logs', methods=['GET'])
def get_logs():
    # Placeholder log data; replace with real logs later
    now = datetime.utcnow()
    logs = [
        {
            'timestamp': (now - timedelta(minutes=i)).isoformat() + 'Z',
            'event': 'Trade Executed' if i % 2 == 0 else 'Order Submitted',
            'details': f'Event details for log {i+1}'
        }
        for i in range(10)
    ]
    return jsonify(logs)

@api_bp.route('/latest_trade_recommendation', methods=['GET'])
def latest_trade_recommendation():
    try:
        # First check if the table exists and has the required columns
        try:
            result = db.session.execute(text("""
                SELECT id, symbol, action, amount, shares, timeframe, expires_at, 
                       required_acceptances, created_at 
                FROM trade_recommendations 
                ORDER BY created_at DESC 
                LIMIT 1
            """)).fetchone()
            
            if result:
                return jsonify({
                    'id': result.id,
                    'symbol': result.symbol,
                    'action': result.action,
                    'status': 'PENDING',  # Default status if column doesn't exist
                    'amount': float(result.amount),
                    'shares': float(result.shares),
                    'timeframe': result.timeframe,
                    'expires_at': result.expires_at.isoformat(),
                    'required_acceptances': result.required_acceptances,
                    'created_at': result.created_at.isoformat(),
                })
            return jsonify({'error': 'No trade recommendations found'}), 404
            
        except Exception as e:
            print(f"Error querying trade_recommendations: {e}")
            return jsonify({'error': 'No trade recommendations found'}), 404
            
    except Exception as e:
        print(f"Error in latest_trade_recommendation: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/trade_acceptances', methods=['POST'])
def post_trade_acceptance():
    data = request.json
    trade_recommendation_id = data.get('trade_recommendation_id')
    user_id = data.get('user_id')
    allocation_amount = data.get('allocation_amount')
    allocation_shares = data.get('allocation_shares')
    status = data.get('status')
    acceptance = TradeAcceptance.query.filter_by(trade_recommendation_id=trade_recommendation_id, user_id=user_id).first()
    if acceptance:
        acceptance.allocation_amount = allocation_amount
        acceptance.allocation_shares = allocation_shares
        acceptance.status = status
        acceptance.updated_at = datetime.utcnow()
    else:
        acceptance = TradeAcceptance(
            trade_recommendation_id=trade_recommendation_id,
            user_id=user_id,
            allocation_amount=allocation_amount,
            allocation_shares=allocation_shares,
            status=status
        )
        db.session.add(acceptance)
    db.session.commit()
    return jsonify({'status': 'success'})

@api_bp.route('/trade_acceptances', methods=['GET'])
def get_trade_acceptances():
    trade_id = request.args.get('trade_id')
    query = TradeAcceptance.query
    if trade_id:
        query = query.filter_by(trade_recommendation_id=trade_id)
    acceptances = query.all()
    result = [
        {
            'user_id': a.user_id,
            'trade_recommendation_id': a.trade_recommendation_id,
            'allocation_amount': float(a.allocation_amount) if a.allocation_amount else None,
            'allocation_shares': float(a.allocation_shares) if a.allocation_shares else None,
            'status': a.status,
            'created_at': a.created_at.isoformat(),
            'updated_at': a.updated_at.isoformat()
        } for a in acceptances
    ]
    return jsonify(result)

@api_bp.route('/trade_execution_log', methods=['GET'])
def get_trade_execution_log():
    trade_id = request.args.get('trade_id')
    query = TradeExecutionLog.query
    if trade_id:
        query = query.filter_by(trade_recommendation_id=trade_id)
    logs = query.order_by(desc(TradeExecutionLog.executed_at)).all()
    result = [
        {
            'trade_recommendation_id': l.trade_recommendation_id,
            'executed_at': l.executed_at.isoformat(),
            'status': l.status,
            'details': l.details
        } for l in logs
    ]
    return jsonify(result)

@api_bp.route('/active_trades', methods=['GET'])
def get_active_trades():
    active = trade_service.get_active_recommendations()
    return jsonify([
        {
            'id': t.id,
            'symbol': t.symbol,
            'action': t.action,
            'status': t.status,
            'amount': float(t.amount),
            'shares': float(t.shares),
            'timeframe': t.timeframe,
            'expires_at': t.expires_at.isoformat(),
            'required_acceptances': t.required_acceptances,
            'created_at': t.created_at.isoformat(),
        } for t in active
    ])

@api_bp.route('/expired_trades', methods=['GET'])
def get_expired_trades():
    expired = trade_service.get_expired_recommendations()
    return jsonify([
        {
            'id': t.id,
            'symbol': t.symbol,
            'action': t.action,
            'status': t.status,
            'amount': float(t.amount),
            'shares': float(t.shares),
            'timeframe': t.timeframe,
            'expires_at': t.expires_at.isoformat(),
            'required_acceptances': t.required_acceptances,
            'created_at': t.created_at.isoformat(),
        } for t in expired
    ])

@api_bp.route('/user_unanswered_trades', methods=['GET'])
def get_user_unanswered_trades():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    active = trade_service.get_active_recommendations()
    answered_ids = {a.trade_recommendation_id for a in TradeAcceptance.query.filter_by(user_id=user_id).all()}
    unanswered = [t for t in active if t.id not in answered_ids]
    return jsonify([
        {
            'id': t.id,
            'symbol': t.symbol,
            'action': t.action,
            'status': t.status,
            'amount': float(t.amount),
            'shares': float(t.shares),
            'timeframe': t.timeframe,
            'expires_at': t.expires_at.isoformat(),
            'required_acceptances': t.required_acceptances,
            'created_at': t.created_at.isoformat(),
        } for t in unanswered
    ])

@api_bp.route('/admin/trigger_expiry_and_execution', methods=['POST'])
def trigger_expiry_and_execution():
    expired = trade_service.expire_recommendations()
    executed = trade_service.execute_eligible_recommendations()
    return jsonify({'expired': expired, 'executed': executed})

@api_bp.route('/admin/create_recommendation', methods=['POST'])
def admin_create_recommendation():
    data = request.json
    symbol = data.get('symbol')
    action = data.get('action')
    amount = float(data.get('amount'))
    shares = float(data.get('shares'))
    timeframe = data.get('timeframe')
    expires_at = datetime.fromisoformat(data.get('expires_at'))
    required_acceptances = int(data.get('required_acceptances', 1))
    rec = trade_service.create_recommendation(symbol, action, amount, shares, timeframe, expires_at, required_acceptances)
    return jsonify({'id': rec.id, 'status': rec.status})

@api_bp.route('/executed_trades', methods=['GET'])
def get_executed_trades():
    executed = TradeRecommendation.query.filter_by(status='EXECUTED').order_by(TradeRecommendation.updated_at.desc()).all()
    return jsonify([
        {
            'id': t.id,
            'symbol': t.symbol,
            'action': t.action,
            'status': t.status,
            'amount': float(t.amount),
            'shares': float(t.shares),
            'timeframe': t.timeframe,
            'expires_at': t.expires_at.isoformat(),
            'required_acceptances': t.required_acceptances,
            'created_at': t.created_at.isoformat(),
            'updated_at': t.updated_at.isoformat(),
        } for t in executed
    ]) 