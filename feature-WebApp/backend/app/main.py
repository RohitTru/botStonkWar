import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

app = create_app()

@app.route("/")
def root():
    return {"message": "Welcome to StockBotWar's WebApp API!"}

@app.route("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)