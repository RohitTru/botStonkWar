import os
from flask import Flask, jsonify

# Entry point for StockBot Brokerage Handler
from app import create_app
from app.models.user import db as user_db
from app.models.position import db as position_db
from app.models.trade import db as trade_db
from app.models.portfolio import db as portfolio_db

app = create_app()

# Initialize all dbs (they share the same instance)
user_db.init_app(app)
position_db.init_app(app)
trade_db.init_app(app)
portfolio_db.init_app(app)

@app.route('/')
def index():
    return {'message': "Welcome to the StockBotWar's StockBot API!"}

@app.route('/health')
def health():
    return {'status': "healthy"}

if __name__ == '__main__':
    app_port = int(os.getenv("APP_PORT", 5000))  # Default to 5000 if env var is missing
    app.run(host='0.0.0.0', port=app_port)