from flask import Blueprint, request, jsonify
from app import db
from app.models.models import TradeRecommendation, TradeAcceptance, UserPosition
from sqlalchemy import desc
from datetime import datetime, timedelta

trades_bp = Blueprint('trades', __name__)

# Get all trade recommendations
@trades_bp.route('/trades', methods=['GET'])
@trades_bp.route('/trades/', methods=['GET'])
def get_trades():
    trades = TradeRecommendation.query.order_by(desc(TradeRecommendation.created_at)).all()
    return jsonify([{
        'id': t.id,
        'symbol': t.symbol,
        'action': t.action,
        'confidence': t.confidence,
        'reasoning': t.reasoning,
        'timeframe': t.timeframe,
        'created_at': t.created_at,
        'strategy_name': t.strategy_name,
        'trade_time': t.trade_time,
        'live_price': t.live_price,
        'live_change_percent': t.live_change_percent,
        'live_volume': t.live_volume
    } for t in trades])

# Get latest trade recommendation
@trades_bp.route('/latest_trade_recommendation', methods=['GET'])
@trades_bp.route('/latest_trade_recommendation/', methods=['GET'])
def get_latest_trade_recommendation():
    rec = TradeRecommendation.query.order_by(desc(TradeRecommendation.created_at)).first()
    if not rec:
        return jsonify({'error': 'No trade recommendations found'}), 404
    return jsonify({
        'id': rec.id,
        'symbol': rec.symbol,
        'action': rec.action,
        'confidence': rec.confidence,
        'reasoning': rec.reasoning,
        'timeframe': rec.timeframe,
        'created_at': rec.created_at,
        'strategy_name': rec.strategy_name,
        'trade_time': rec.trade_time,
        'live_price': rec.live_price,
        'live_change_percent': rec.live_change_percent,
        'live_volume': rec.live_volume
    })

# Trade acceptances
@trades_bp.route('/trade_acceptances', methods=['GET', 'POST'])
@trades_bp.route('/trade_acceptances/', methods=['GET', 'POST'])
def trade_acceptances():
    if request.method == 'POST':
        data = request.get_json()
        # Validate status
        if data.get('status') not in ('ACCEPTED', 'DENIED'):
            return jsonify({'error': 'Invalid status, must be ACCEPTED or DENIED'}), 400
        # Validate allocation for ACCEPTED
        if data['status'] == 'ACCEPTED':
            alloc_amt = data.get('allocation_amount')
            alloc_shares = data.get('allocation_shares')
            if not ((alloc_amt is not None and float(alloc_amt) > 0) or (alloc_shares is not None and float(alloc_shares) > 0)):
                return jsonify({'error': 'Must allocate amount or shares for acceptance'}), 400
        acceptance = TradeAcceptance(
            user_id=data['user_id'],
            trade_id=data['trade_id'],
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
@trades_bp.route('/user_positions/', methods=['GET'])
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

@trades_bp.route('/user_trade_recommendations', methods=['GET'])
def user_trade_recommendations():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    now = datetime.utcnow()
    # Fetch all trades, not just PENDING
    trades = TradeRecommendation.query.order_by(desc(TradeRecommendation.created_at)).all()
    acceptances = TradeAcceptance.query.filter_by(user_id=user_id).all()
    acceptance_map = {(a.trade_id, a.user_id): a for a in acceptances}
    result = []
    for t in trades:
        # Expiry logic
        expires_at = t.expires_at
        if t.timeframe and t.timeframe.lower() in ['short_term', 'short term'] and t.created_at:
            expires_at = t.created_at + timedelta(minutes=2)
        is_expired = expires_at and expires_at < now
        acceptance = acceptance_map.get((t.id, int(user_id)))
        user_status = acceptance.status if acceptance else 'PENDING'
        is_active = (t.status == 'PENDING') and not is_expired and user_status == 'PENDING'
        # Include all trades (active, expired, and responded)
        result.append({
            'id': t.id,
            'symbol': t.symbol,
            'action': t.action,
            'confidence': t.confidence,
            'reasoning': t.reasoning,
            'timeframe': t.timeframe,
            'created_at': t.created_at,
            'strategy_name': t.strategy_name,
            'trade_time': t.trade_time,
            'live_price': t.live_price,
            'live_change_percent': t.live_change_percent,
            'live_volume': t.live_volume,
            'expires_at': expires_at,
            'status': t.status,
            'user_status': user_status,
            'is_active': is_active,
            'is_expired': is_expired,
            'acceptance_id': acceptance.id if acceptance else None,
            'allocation_amount': acceptance.allocation_amount if acceptance else None,
            'allocation_shares': acceptance.allocation_shares if acceptance else None,
            'acceptance_created_at': acceptance.created_at if acceptance else None
        })
    return jsonify(result) 