from flask import Blueprint, request, jsonify
from app.services.trade_service import TradeService
from app.services.alpaca_service import AlpacaService
from app.models.user import User
from app.database import db
from sqlalchemy.exc import NoResultFound
from datetime import datetime, timedelta

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
    user_count = db.session.query(User).count()
    # Fetch live balance from Alpaca
    alpaca = AlpacaService()
    account = alpaca.api.get_account()
    portfolio_value = float(account.portfolio_value)
    metrics = {
        'portfolio_value': portfolio_value,
        'pnl': 2500.00,  # Placeholder
        'active_users': user_count
    }
    return jsonify(metrics)

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