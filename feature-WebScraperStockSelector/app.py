import os
from dotenv import load_dotenv
from app import create_app

# Load environment variables
load_dotenv()

# Create Flask app
app = create_app()

# Set configuration from environment variables
app.config.update(
    MYSQL_HOST=os.getenv('MYSQL_HOST', 'mysql'),
    MYSQL_USER=os.getenv('MYSQL_USER'),
    MYSQL_PASSWORD=os.getenv('MYSQL_PASSWORD'),
    MYSQL_SCRAPING_DATABASE=os.getenv('MYSQL_SCRAPING_DATABASE', 'bot_stonk_war_scraping')
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('APP_PORT', 5004)))