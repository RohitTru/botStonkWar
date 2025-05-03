from flask import jsonify

@app.route('/api/strategy-status')
def strategy_status():
    strategies = strategy_manager.get_all_strategies()
    return jsonify({"strategies": strategies})

@app.route('/api/strategy-activation', methods=['POST'])
def set_strategy_activation():
    data = request.json
    name = data.get('name')
    active = data.get('active')
    app.logger.info(f"Setting strategy {name} activation to {active}")
    strategy_manager.set_active(name, active)
    app.logger.info(f"Strategy {name} activation set to {active}")
    return jsonify({"status": "success", "name": name, "active": active}) 