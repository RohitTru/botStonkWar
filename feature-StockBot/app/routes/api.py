from flask import Blueprint, request, jsonify
from app.services.trade_service import TradeService
from app.models.user import User
from app.database import db

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
    # Get real user count from the database
    user_count = db.session.query(User).count()
    metrics = {
        'portfolio_value': 100000.00,  # Placeholder, update with real value if needed
        'pnl': 2500.00,                # Placeholder
        'active_users': user_count
    }
    return jsonify(metrics)

@api_bp.route('/brokerage/add_funds', methods=['POST'])
def add_funds():
    data = request.json
    amount = data.get('amount')
    # Simulate adding funds (in real Alpaca, this is not possible in paper trading)
    # You could update a local brokerage balance in your DB for dashboard purposes
    # For now, just return success
    return jsonify({'status': 'success', 'added': amount}) 