from flask import Flask
import logging
from routes import routes
from flask_apscheduler import APScheduler
from analyzer_manager import AnalyzerManager
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
scheduler = APScheduler()
db = Database()
analyzer_manager = AnalyzerManager(db)

def process_articles():
    """Background task to process pending articles"""
    try:
        count = analyzer_manager.process_pending_articles()
        if count > 0:
            logger.info(f"Processed {count} articles")
    except Exception as e:
        logger.error(f"Error in background task: {str(e)}")

def create_app():
    app = Flask(__name__)
    app.register_blueprint(routes)
    
    # Configure scheduler
    app.config['SCHEDULER_API_ENABLED'] = True
    scheduler.init_app(app)
    scheduler.add_job(id='process_articles', 
                     func=process_articles,
                     trigger='interval', 
                     seconds=30)  # Process every 30 seconds
    scheduler.start()
    
    return app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True) 