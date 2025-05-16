from flask import Blueprint, request, jsonify
from app import db
from app.models.models import TradeRecommendation, TradeAcceptance, UserPosition, User, TradeExecutionLog
from sqlalchemy import desc
from datetime import datetime, timedelta
import os
import requests

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
        # Validate allocation for ACCEPTED (dollar only)
        if data['status'] == 'ACCEPTED':
            alloc_amt = data.get('allocation_amount')
            if alloc_amt is None or float(alloc_amt) <= 0:
                return jsonify({'error': 'Must allocate a positive dollar amount for acceptance'}), 400
        acceptance = TradeAcceptance(
            user_id=data['user_id'],
            trade_id=data['trade_id'],
            allocation_amount=data.get('allocation_amount'),
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
    # Fetch user positions for SELL filtering
    user_positions = UserPosition.query.filter_by(user_id=user_id).all()
    user_symbols = set(p.symbol for p in user_positions)
    result = []
    for t in trades:
        # Expiry logic
        expires_at = t.expires_at
        if t.timeframe and t.timeframe.lower() in ['short_term', 'short term'] and t.created_at:
            expires_at = t.created_at + timedelta(minutes=2)
        is_expired = expires_at and expires_at < now
        acceptance = acceptance_map.get((t.id, int(user_id)))
        user_status = acceptance.status if acceptance else 'PENDING'
        # Check for failed execution
        failed_log = TradeExecutionLog.query.filter_by(trade_recommendation_id=t.id, status='FAILED').first()
        if acceptance and failed_log:
            user_status = 'FAILED'
        is_active = (t.status == 'PENDING') and not is_expired and user_status == 'PENDING'
        # Only recommend SELL trades if user owns the symbol (clarified)
        if t.action == 'SELL' and t.symbol not in user_symbols:
            continue
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

@trades_bp.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([
        {
            'id': u.id,
            'username': u.username,
            'balance': u.balance
        } for u in users
    ])

@trades_bp.route('/api/live_price', methods=['GET'])
def get_live_price():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({'error': 'symbol required'}), 400
    alpaca_key = os.environ.get('ALPACA_KEY')
    alpaca_secret = os.environ.get('ALPACA_SECRET')
    if not alpaca_key or not alpaca_secret:
        return jsonify({'error': 'Alpaca API credentials not set'}), 500
    url = f'https://paper-api.alpaca.markets/v2/stocks/{symbol}/quotes/latest'
    headers = {
        'APCA-API-KEY-ID': alpaca_key,
        'APCA-API-SECRET-KEY': alpaca_secret
    }
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        if resp.status_code != 200:
            return jsonify({'error': f'Alpaca API error: {resp.text}'}), 502
        data = resp.json()
        # The latest price is in the 'ap' (ask price) or 'bp' (bid price) or 'p' (price) field
        price = None
        if 'quote' in data:
            price = data['quote'].get('ap') or data['quote'].get('bp') or data['quote'].get('p')
        if price is None:
            return jsonify({'error': 'No price found for symbol'}), 404
        return jsonify({'symbol': symbol, 'price': float(price)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@trades_bp.route('/api/user_equity', methods=['GET'])
def user_equity():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    # Get user positions
    positions = UserPosition.query.filter_by(user_id=user_id).all()
    # Get live prices for all symbols
    symbols = [p.symbol for p in positions]
    prices = {}
    alpaca_key = os.environ.get('ALPACA_KEY')
    alpaca_secret = os.environ.get('ALPACA_SECRET')
    for symbol in symbols:
        try:
            url = f'https://paper-api.alpaca.markets/v2/stocks/{symbol}/quotes/latest'
            headers = {
                'APCA-API-KEY-ID': alpaca_key,
                'APCA-API-SECRET-KEY': alpaca_secret
            }
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                price = None
                if 'quote' in data:
                    price = data['quote'].get('ap') or data['quote'].get('bp') or data['quote'].get('p')
                if price:
                    prices[symbol] = float(price)
        except Exception:
            pass
    # Calculate equity
    equity = 0
    breakdown = {}
    for p in positions:
        price = prices.get(p.symbol, 0)
        value = p.shares * price
        equity += value
        breakdown[p.symbol] = {'shares': p.shares, 'price': price, 'value': value}
    # Pending allocations (PENDING acceptances not yet executed or failed)
    from app.models.models import TradeAcceptance, TradeRecommendation, TradeExecutionLog
    pending_acceptances = TradeAcceptance.query.filter_by(user_id=user_id, status='ACCEPTED').all()
    pending_total = 0
    for acc in pending_acceptances:
        trade = TradeRecommendation.query.filter_by(id=acc.trade_id).first()
        if not trade or trade.status != 'PENDING':
            continue
        # Check if this trade has a FAILED execution log
        failed_log = TradeExecutionLog.query.filter_by(trade_recommendation_id=trade.id, status='FAILED').first()
        if failed_log:
            continue  # skip, funds should be returned
        amt = acc.allocation_amount or 0
        price = prices.get(trade.symbol, 0)
        pending_total += float(amt)
    total = equity + pending_total
    return jsonify({
        'equity': equity,
        'pending_allocations': pending_total,
        'total': total,
        'breakdown': breakdown
    }) 