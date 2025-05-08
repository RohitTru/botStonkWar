# Entry point for StockBot Brokerage Handler
from app import create_app

app = create_app()

@app.route('/')
def index():
    return {'message': "Welcome to the StockBotWar's StockBot API!"}

@app.route('/health')
def health():
    return {'status': "healthy"}

if __name__ == '__main__':
    import os
    app_port = int(os.getenv("APP_PORT", 5000))
    app.run(host='0.0.0.0', port=app_port)