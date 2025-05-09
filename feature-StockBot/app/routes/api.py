from flask import Blueprint, request, jsonify
from app.services.trade_service import TradeService
from app.services.alpaca_service import AlpacaService
from app.models.user import User
from app.database import db
from sqlalchemy.exc import NoResultFound
from datetime import datetime, timedelta
from app.models.trade import TradeAcceptance, TradeExecutionLog, TradeRecommendation
from sqlalchemy import desc, text
from decimal import Decimal

api_bp = Blueprint('api', __name__)
trade_service = TradeService()

def safe_float(val):
    if isinstance(val, Decimal):
        return float(val)
    return float(val) if isinstance(val, (int, float)) else 0.0

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
    metrics = {
        'portfolio_value': 0.0,
        'pnl': 0.0,
        'active_users': 0,
        'total_trades': 0,
        'executed_trades': 0,
        'pending_trades': 0,
        'expired_trades': 0,
        'failed_trades': 0,
        'total_allocations': 0.0,
        'total_users': 0,
        'avg_acceptance_time': 0,
        'acceptance_rate': 0,
        'avg_trade_size': 0,
        'current_acceptances': 0,
        'avg_execution_time': 0
    }
    # Individual metric try/except blocks
    try:
        metrics['active_users'] = db.session.query(db.func.count(User.id)).scalar()
    except Exception as e:
        print(f"Error fetching active_users: {e}")
    try:
        metrics['total_trades'] = db.session.query(db.func.count(TradeRecommendation.id)).scalar()
    except Exception as e:
        print(f"Error fetching total_trades: {e}")
    try:
        metrics['executed_trades'] = db.session.query(db.func.count(TradeRecommendation.id)).filter(TradeRecommendation.status == 'EXECUTED').scalar()
    except Exception as e:
        print(f"Error fetching executed_trades: {e}")
    try:
        metrics['pending_trades'] = db.session.query(db.func.count(TradeRecommendation.id)).filter(TradeRecommendation.status == 'PENDING').scalar()
    except Exception as e:
        print(f"Error fetching pending_trades: {e}")
    try:
        metrics['expired_trades'] = db.session.query(db.func.count(TradeRecommendation.id)).filter(TradeRecommendation.status == 'EXPIRED').scalar()
    except Exception as e:
        print(f"Error fetching expired_trades: {e}")
    try:
        metrics['failed_trades'] = db.session.execute(text('SELECT COUNT(*) FROM trade_execution_log WHERE status = "FAILED"')).scalar()
    except Exception as e:
        print(f"Error fetching failed_trades: {e}")
    try:
        metrics['total_allocations'] = float(db.session.execute(text('SELECT COALESCE(SUM(allocation_amount),0) FROM trade_acceptances WHERE status = "ACCEPTED"')).scalar() or 0)
    except Exception as e:
        print(f"Error fetching total_allocations: {e}")
    try:
        metrics['total_users'] = db.session.query(db.func.count(User.id)).scalar()
    except Exception as e:
        print(f"Error fetching total_users: {e}")
    try:
        metrics['avg_acceptance_time'] = round(db.session.execute(text('''
            SELECT AVG(TIMESTAMPDIFF(SECOND, created_at, updated_at))
            FROM trade_acceptances 
            WHERE status = 'ACCEPTED'
        ''')).scalar() or 0, 2)
    except Exception as e:
        print(f"Error fetching avg_acceptance_time: {e}")
    try:
        metrics['acceptance_rate'] = db.session.execute(text('''
            SELECT 
                ROUND(COUNT(CASE WHEN status = 'ACCEPTED' THEN 1 END) / 
                NULLIF(COUNT(*), 0) * 100, 2)
            FROM trade_acceptances
        ''')).scalar() or 0
    except Exception as e:
        print(f"Error fetching acceptance_rate: {e}")
    try:
        metrics['avg_trade_size'] = round(db.session.execute(text('''
            SELECT AVG(amount) 
            FROM trade_recommendations 
            WHERE status = 'EXECUTED'
        ''')).scalar() or 0, 2)
    except Exception as e:
        print(f"Error fetching avg_trade_size: {e}")
    try:
        metrics['current_acceptances'] = db.session.execute(text('''
            SELECT COUNT(*) 
            FROM trade_acceptances 
            WHERE status = 'ACCEPTED' 
            AND trade_recommendation_id IN (
                SELECT id FROM trade_recommendations WHERE status = 'PENDING'
            )
        ''')).scalar() or 0
    except Exception as e:
        print(f"Error fetching current_acceptances: {e}")
    try:
        # Fix: join trade_execution_log and trade_recommendations for avg_execution_time
        metrics['avg_execution_time'] = round(db.session.execute(text('''
            SELECT AVG(TIMESTAMPDIFF(SECOND, tr.created_at, tel.executed_at))
            FROM trade_execution_log tel
            JOIN trade_recommendations tr ON tel.trade_recommendation_id = tr.id
            WHERE tel.status = 'EXECUTED'
        ''')).scalar() or 0, 2)
    except Exception as e:
        print(f"Error fetching avg_execution_time: {e}")
    try:
        alpaca = AlpacaService()
        account = alpaca.api.get_account()
        metrics['portfolio_value'] = float(account.portfolio_value)
        metrics['pnl'] = float(account.equity) - float(account.last_equity)
    except Exception as e:
        print(f"Error fetching Alpaca data: {e}")
        metrics['portfolio_value'] = 0.0
        metrics['pnl'] = 0.0
    # Ensure all values are JSON serializable
    for k, v in metrics.items():
        metrics[k] = safe_float(v)
    return jsonify(metrics)

@api_bp.route('/brokerage/add_funds', methods=['POST'])
def add_funds():
    data = request.json
    amount = float(data.get('amount', 0))
    # This is a simulation; does not affect Alpaca
    return jsonify({'status': 'success', 'added': amount, 'new_balance': 'live from Alpaca'})

@api_bp.route('/users', methods=['GET'])
def get_users():
    try:
        search = request.args.get('search', '').strip()
        sort = request.args.get('sort', 'equity')
        pnl_filter = request.args.get('pnl_filter', 'all')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        query = db.session.query(User)
        if search:
            query = query.filter(User.username.ilike(f'%{search}%'))
        users = query.order_by(User.balance.desc()).all()
        user_list = []
        for u in users:
            positions = db.session.execute(text('SELECT shares, symbol FROM user_positions WHERE user_id = :uid'), {'uid': u.id}).fetchall()
            equity = float(u.balance) if u.balance else 0.0
            pnl = 0.0
            for pos in positions:
                shares = float(pos.shares)
                equity += 0
                pnl += 0
            user_list.append({
                'id': u.id,
                'username': u.username,
                'equity': round(equity, 2),
                'pnl': round(pnl, 2),
            })
        # Filtering
        if pnl_filter == 'positive':
            user_list = [u for u in user_list if u['pnl'] > 0]
        elif pnl_filter == 'negative':
            user_list = [u for u in user_list if u['pnl'] < 0]
        # Sorting
        if sort == 'equity':
            user_list.sort(key=lambda x: x['equity'], reverse=True)
        elif sort == 'pnl':
            user_list.sort(key=lambda x: x['pnl'], reverse=True)
        elif sort == 'username':
            user_list.sort(key=lambda x: x['username'])
        # Pagination
        total = len(user_list)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = user_list[start:end]
        return jsonify({'total': total, 'users': paginated})
    except Exception as e:
        print(f"Error in get_users: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@api_bp.route('/trades', methods=['GET'])
def get_trades():
    search = request.args.get('search', '').strip()
    status = request.args.get('status', '').strip()
    symbol = request.args.get('symbol', '').strip()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    query = TradeRecommendation.query
    if search:
        query = query.filter(TradeRecommendation.symbol.ilike(f'%{search}%'))
    if status:
        query = query.filter(TradeRecommendation.status == status)
    if symbol:
        query = query.filter(TradeRecommendation.symbol == symbol)
    if start_date:
        query = query.filter(TradeRecommendation.created_at >= start_date)
    if end_date:
        query = query.filter(TradeRecommendation.created_at <= end_date)
    total = query.count()
    trades = query.order_by(TradeRecommendation.created_at.desc()).offset((page-1)*per_page).limit(per_page).all()
    trade_list = []
    for t in trades:
        user_count = TradeAcceptance.query.filter_by(trade_recommendation_id=t.id, status='ACCEPTED').count()
        # Use all fields from the schema
        live_price = getattr(t, 'live_price', None)
        shares = float(getattr(t, 'shares', 0) or 0)
        action = getattr(t, 'action', '')
        brokerage_trade = f"{action} {shares:.4f} shares at ${float(live_price):.2f}" if live_price is not None else ''
        # Expired At logic
        expired_at = ''
        if t.timeframe and t.timeframe.lower() in ['short_term', 'short term'] and t.created_at:
            expired_at_dt = t.created_at + timedelta(minutes=2)
            expired_at = expired_at_dt.isoformat()
        elif hasattr(t, 'expires_at') and t.expires_at:
            expired_at = t.expires_at.isoformat()
        trade_list.append({
            'id': t.id,
            'symbol': t.symbol,
            'action': t.action,
            'confidence': getattr(t, 'confidence', None),
            'reasoning': getattr(t, 'reasoning', None),
            'timeframe': t.timeframe,
            'metadata': getattr(t, 'metadata', None),
            'created_at': t.created_at.isoformat() if t.created_at else '',
            'strategy_name': getattr(t, 'strategy_name', ''),
            'trade_time': getattr(t, 'trade_time', None),
            'live_price': float(live_price) if live_price is not None else None,
            'live_change_percent': getattr(t, 'live_change_percent', None),
            'live_volume': getattr(t, 'live_volume', None),
            'status': t.status,
            'amount': float(getattr(t, 'amount', 0) or 0),
            'shares': shares,
            'expires_at': t.expires_at.isoformat() if hasattr(t, 'expires_at') and t.expires_at else '',
            'required_acceptances': getattr(t, 'required_acceptances', None),
            'updated_at': t.updated_at.isoformat() if hasattr(t, 'updated_at') and t.updated_at else '',
            'users': user_count,
            'price': float(live_price) if live_price is not None else None,
            'brokerage_trade': brokerage_trade,
            'expired_at': expired_at,
        })
    return jsonify({'total': total, 'trades': trade_list})

@api_bp.route('/orders', methods=['GET'])
def get_orders():
    status = request.args.get('status', '').strip()
    symbol = request.args.get('symbol', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    alpaca = AlpacaService()
    orders = alpaca.api.list_orders(status='all', limit=200)
    # Filter in memory since Alpaca API doesn't support all filters
    if status:
        orders = [o for o in orders if o.status == status]
    if symbol:
        orders = [o for o in orders if o.symbol == symbol]
    total = len(orders)
    paginated = orders[(page-1)*per_page:page*per_page]
    order_list = [
        {
            'symbol': o.symbol,
            'qty': o.qty,
            'side': o.side,
            'status': o.status,
            'filled_avg_price': o.filled_avg_price,
            'submitted_at': o.submitted_at.isoformat() if o.submitted_at else '',
        } for o in paginated
    ]
    return jsonify({'total': total, 'orders': order_list})

@api_bp.route('/logs', methods=['GET'])
def get_logs():
    event = request.args.get('event', '').strip()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    base_query = 'SELECT trade_recommendation_id, executed_at, status, details FROM trade_execution_log WHERE 1=1'
    params = {}
    if event:
        base_query += ' AND status = :event'
        params['event'] = event
    if start_date:
        base_query += ' AND executed_at >= :start_date'
        params['start_date'] = start_date
    if end_date:
        base_query += ' AND executed_at <= :end_date'
        params['end_date'] = end_date
    base_query += ' ORDER BY executed_at DESC'
    count_query = f'SELECT COUNT(*) FROM ({base_query}) as sub'
    total = db.session.execute(text(count_query), params).scalar()
    base_query += ' LIMIT :limit OFFSET :offset'
    params['limit'] = per_page
    params['offset'] = (page-1)*per_page
    logs = db.session.execute(text(base_query), params).fetchall()
    log_list = []
    for l in logs:
        log_list.append({
            'timestamp': l.executed_at.isoformat() if l.executed_at else '',
            'event': l.status,
            'details': l.details,
            'trade_recommendation_id': l.trade_recommendation_id,
        })
    return jsonify({'total': total, 'logs': log_list})

@api_bp.route('/latest_trade_recommendation', methods=['GET'])
def latest_trade_recommendation():
    try:
        try:
            db.session.execute(text("SELECT 1 FROM trade_recommendations LIMIT 1"))
        except Exception as e:
            print(f"Table trade_recommendations does not exist: {e}")
            return jsonify({'error': 'No trade recommendations found'}), 404
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
                    'status': 'PENDING',
                    'amount': float(result.amount),
                    'shares': float(result.shares),
                    'timeframe': result.timeframe,
                    'expires_at': result.expires_at.isoformat() if result.expires_at else '',
                    'required_acceptances': result.required_acceptances,
                    'created_at': result.created_at.isoformat() if result.created_at else '',
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
    # Join with User table for username
    user_ids = [a.user_id for a in acceptances]
    users = {u.id: u.username for u in User.query.filter(User.id.in_(user_ids)).all()}
    result = [
        {
            'user_id': a.user_id,
            'username': users.get(a.user_id, ''),
            'trade_recommendation_id': a.trade_recommendation_id,
            'allocation_amount': float(a.allocation_amount) if a.allocation_amount else None,
            'allocation_shares': float(a.allocation_shares) if a.allocation_shares else None,
            'status': a.status,
            'created_at': a.created_at.isoformat() if a.created_at else '',
            'updated_at': a.updated_at.isoformat() if a.updated_at else ''
        } for a in acceptances
    ]
    return jsonify(result)

@api_bp.route('/trade_execution_log', methods=['GET'])
def get_trade_execution_log():
    trade_id = request.args.get('trade_id')
    base_query = 'SELECT id, trade_recommendation_id, executed_at, status, details FROM trade_execution_log WHERE 1=1'
    params = {}
    if trade_id:
        base_query += ' AND trade_recommendation_id = :trade_id'
        params['trade_id'] = trade_id
    base_query += ' ORDER BY executed_at DESC'
    logs = db.session.execute(text(base_query), params).fetchall()
    result = []
    for l in logs:
        result.append({
            'id': l.id,
            'trade_recommendation_id': l.trade_recommendation_id,
            'executed_at': l.executed_at.isoformat() if l.executed_at else '',
            'status': l.status,
            'details': l.details,
        })
    return jsonify(result)

@api_bp.route('/failed_trades', methods=['GET'])
def get_failed_trades():
    trade_id = request.args.get('trade_id')
    user_id = request.args.get('user_id')
    base_query = 'SELECT id, trade_recommendation_id, user_id, reason, failed_at FROM failed_trades WHERE 1=1'
    params = {}
    if trade_id:
        base_query += ' AND trade_recommendation_id = :trade_id'
        params['trade_id'] = trade_id
    if user_id:
        base_query += ' AND user_id = :user_id'
        params['user_id'] = user_id
    base_query += ' ORDER BY failed_at DESC'
    logs = db.session.execute(text(base_query), params).fetchall()
    result = []
    for l in logs:
        result.append({
            'id': l.id,
            'trade_recommendation_id': l.trade_recommendation_id,
            'user_id': l.user_id,
            'reason': l.reason,
            'failed_at': l.failed_at.isoformat() if l.failed_at else '',
        })
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

@api_bp.route('/user/<int:user_id>/positions', methods=['GET'])
def get_user_positions(user_id):
    try:
        positions = db.session.execute(text('SELECT symbol, shares FROM user_positions WHERE user_id = :uid'), {'uid': user_id}).fetchall()
        pos_list = []
        for pos in positions:
            pos_list.append({
                'symbol': pos.symbol,
                'shares': float(pos.shares),
                'current_price': None,
                'market_value': None,
            })
        return jsonify(pos_list)
    except Exception as e:
        print(f"Error in get_user_positions: {e}")
        return jsonify([])

@api_bp.route('/user/<int:user_id>/history', methods=['GET'])
def get_user_history(user_id):
    try:
        history = db.session.execute(text('SELECT symbol, shares_owned, average_price, market_price, total_value, unrealized_pnl, recorded_at FROM historical_positions WHERE user_id = :uid ORDER BY recorded_at DESC'), {'uid': user_id}).fetchall()
        hist_list = []
        for h in history:
            hist_list.append({
                'symbol': h.symbol,
                'shares_owned': float(h.shares_owned),
                'average_price': float(h.average_price),
                'market_price': float(h.market_price),
                'total_value': float(h.total_value),
                'unrealized_pnl': float(h.unrealized_pnl),
                'recorded_at': h.recorded_at.isoformat() if h.recorded_at else '',
            })
        return jsonify(hist_list)
    except Exception as e:
        print(f"Error in get_user_history: {e}")
        return jsonify([])

@api_bp.route('/brokerage/positions', methods=['GET'])
def get_brokerage_positions():
    try:
        positions = db.session.execute(text('SELECT symbol, total_shares, average_price, current_price, total_value, unrealized_pnl, updated_at FROM brokerage_summary ORDER BY total_value DESC')).fetchall()
        pos_list = []
        for pos in positions:
            pos_list.append({
                'symbol': pos.symbol,
                'total_shares': float(pos.total_shares),
                'average_price': float(pos.average_price),
                'current_price': float(pos.current_price),
                'total_value': float(pos.total_value),
                'unrealized_pnl': float(pos.unrealized_pnl),
                'updated_at': pos.updated_at.isoformat() if pos.updated_at else '',
            })
        return jsonify(pos_list)
    except Exception as e:
        print(f"Error in get_brokerage_positions: {e}")
        return jsonify([])

@api_bp.route('/brokerage/history', methods=['GET'])
def get_brokerage_history():
    try:
        history = db.session.execute(text('SELECT symbol, shares_owned, average_price, market_price, total_value, unrealized_pnl, recorded_at FROM historical_positions ORDER BY recorded_at DESC')).fetchall()
        hist_list = []
        for h in history:
            hist_list.append({
                'symbol': h.symbol,
                'shares_owned': float(h.shares_owned),
                'average_price': float(h.average_price),
                'market_price': float(h.market_price),
                'total_value': float(h.total_value),
                'unrealized_pnl': float(h.unrealized_pnl),
                'recorded_at': h.recorded_at.isoformat() if h.recorded_at else '',
            })
        return jsonify(hist_list)
    except Exception as e:
        print(f"Error in get_brokerage_history: {e}")
        return jsonify([]) 