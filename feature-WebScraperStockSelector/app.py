import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify(message="Welcome to the StockBotWar's WebScraperStockSelector API!")

@app.route('/health')
def health():
    return jsonify(status="healthy")

if __name__ == '__main__':
    app_port = int(os.getenv("APP_PORT", 5000))  # Default to 5000 if env var is missing
    app.run(host='0.0.0.0', port=app_port)