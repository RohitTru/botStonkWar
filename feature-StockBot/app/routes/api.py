from flask import Blueprint, request, jsonify
from app.services.trade_service import TradeService
from app.services.alpaca_service import AlpacaService
from app.models.user import User
from app.database import db
from sqlalchemy.exc import NoResultFound

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