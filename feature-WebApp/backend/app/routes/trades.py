from flask import Blueprint, request, jsonify
from app import db
from app.models.models import Trade, TradeAcceptance, UserPosition
from sqlalchemy import desc

trades_bp = Blueprint('trades', __name__)

# Get all trades
@trades_bp.route('/trades', methods=['GET'])
def get_trades():
    trades = Trade.query.order_by(desc(Trade.created_at)).all()
    return jsonify([{
        'id': t.id,
        'strategy_id': t.strategy_id if hasattr(t, 'strategy_id') else None,
        'stock_symbol': t.stock_symbol,
        'trade_type': t.trade_type,
        'status': t.status,
        'entry_price': t.entry_price,
        'exit_price': t.exit_price,
        'quantity': t.quantity,
        'created_at': t.created_at,
        'executed_at': getattr(t, 'executed_at', None),
        'closed_at': getattr(t, 'closed_at', None)
    } for t in trades])

# Get latest trade recommendation
@trades_bp.route('/latest_trade_recommendation', methods=['GET'])
def get_latest_trade_recommendation():
    trade = Trade.query.order_by(desc(Trade.created_at)).first()
    if not trade:
        return jsonify({'error': 'No trade recommendations found'}), 404
    return jsonify({
        'id': trade.id,
        'strategy_id': trade.strategy_id if hasattr(trade, 'strategy_id') else None,
        'stock_symbol': trade.stock_symbol,
        'trade_type': trade.trade_type,
        'status': trade.status,
        'entry_price': trade.entry_price,
        'exit_price': trade.exit_price,
        'quantity': trade.quantity,
        'created_at': trade.created_at,
        'executed_at': getattr(trade, 'executed_at', None),
        'closed_at': getattr(trade, 'closed_at', None)
    })

# Trade acceptances
@trades_bp.route('/trade_acceptances', methods=['GET', 'POST'])
def trade_acceptances():
    if request.method == 'POST':
        data = request.get_json()
        acceptance = TradeAcceptance(
            user_id=data['user_id'],
            trade_id=data['trade_recommendation_id'],
            allocation_amount=data.get('allocation_amount'),
            allocation_shares=data.get('allocation_shares'),
            status=data['status']
        )
        db.session.add(acceptance)
        db.session.commit()
        return jsonify({'message': 'Acceptance recorded', 'id': acceptance.id}), 201
    else:
        trade_id = request.args.get('trade_id')
        user_id = request.args.get('user_id')
        query = TradeAcceptance.query
        if trade_id:
            query = query.filter_by(trade_id=trade_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        acceptances = query.order_by(desc(TradeAcceptance.created_at)).all()
        return jsonify([{
            'id': a.id,
            'user_id': a.user_id,
            'trade_id': a.trade_id,
            'allocation_amount': a.allocation_amount,
            'allocation_shares': a.allocation_shares,
            'status': a.status,
            'created_at': a.created_at
        } for a in acceptances])

# User positions
@trades_bp.route('/user_positions', methods=['GET'])
def user_positions():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    positions = UserPosition.query.filter_by(user_id=user_id).all()
    return jsonify([{
        'id': p.id,
        'user_id': p.user_id,
        'symbol': p.symbol,
        'shares': p.shares,
        'updated_at': p.updated_at
    } for p in positions]) 