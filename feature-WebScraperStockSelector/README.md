# Stock Market News Scraper

## Overview
This service is part of the BotStonkWar microservices architecture, specifically handling the collection and storage of stock market-related news articles. It continuously monitors financial news sources and stores relevant articles in a MySQL database for analysis by other services.

## Architecture

### Core Components

1. **Web Scraper**
   - Located in `app/scrapers/`
   - Currently implements Yahoo Finance scraping
   - Extensible architecture for adding new sources
   - Uses BeautifulSoup4 for HTML parsing
   - Implements rate limiting and error handling

2. **Database Layer**
   - MySQL database for persistent storage
   - Two main tables:
     - `articles`: Stores article content and metadata
     - `scraping_logs`: Tracks scraping attempts and errors
   - Handles connection pooling and retry logic

3. **API Layer**
   - Flask-based REST API
   - Endpoints for:
     - Retrieving recent articles
     - Viewing scraping logs
     - Managing article deletion
     - Health checks

## Database Schema

### Articles Table
```sql
CREATE TABLE articles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    link VARCHAR(500) UNIQUE NOT NULL,
    content TEXT,
    source VARCHAR(100),
    published_date DATETIME,
    scraped_date DATETIME,
    symbols JSON,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Scraping Logs Table
```sql
CREATE TABLE scraping_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    status VARCHAR(50) NOT NULL,
    source_type VARCHAR(100),
    url VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Adding a New Scraper

To add a new scraper for a different news source:

1. Create a new file in `app/scrapers/` (e.g., `reuters_scraper.py`)
2. Implement the scraper class following this template:

```python
from app.database import Database
from datetime import datetime
import logging

class ReutersScraper:
    def __init__(self):
        self.db = Database()
        self.seen_urls = set()
        self.logger = logging.getLogger(__name__)

    def scrape_article(self, url):
        """
        Implement article scraping logic here.
        Returns: dict with keys:
            - content: article text
            - symbols: list of stock symbols
        """
        pass

    def scrape_feed(self):
        """
        Implement feed scraping logic here.
        Should:
        1. Get list of articles
        2. For each new article:
           - Scrape content
           - Extract symbols
           - Save to database
           - Log the attempt
        """
        pass

    def run(self):
        """
        Main loop - typically don't need to modify
        """
        while True:
            try:
                self.scrape_feed()
                time.sleep(300)  # 5 minute delay
            except Exception as e:
                self.logger.error(f"Error in scraper run loop: {e}")
                time.sleep(60)
```

3. Register your scraper in `app/scrapers/__init__.py`
4. Add any new dependencies to `requirements.txt`

## Best Practices for Scrapers

1. **Rate Limiting**
   - Implement delays between requests
   - Use random intervals to avoid detection
   - Respect robots.txt

2. **Error Handling**
   - Log all errors with context
   - Implement retries for transient failures
   - Handle network timeouts gracefully

3. **Data Cleaning**
   - Remove HTML tags properly
   - Handle character encodings
   - Normalize stock symbols

4. **Resource Management**
   - Close connections properly
   - Implement timeouts
   - Monitor memory usage

## Deployment

The service is containerized using Docker and can be deployed using Docker Compose:

```yaml
webscraper-selector:
    image: rohittru/bot-stonk-war:feature-WebScraperStockSelector
    environment:
      - MYSQL_HOST=mysql
      - MYSQL_PORT=3306
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    ports:
      - "5004:5004"
```

### Environment Variables
- `MYSQL_HOST`: Database host
- `MYSQL_PORT`: Database port
- `MYSQL_USER`: Database user (set in Portainer)
- `MYSQL_PASSWORD`: Database password (set in Portainer)
- `MYSQL_DB`: Database name (set in Portainer)
- `REDIS_HOST`: Redis host
- `REDIS_PORT`: Redis port
- `LOG_LEVEL`: Logging level
- `SCRAPE_INTERVAL`: Time between scrapes in seconds

## Monitoring

The service provides several monitoring endpoints:

- `/health`: Basic health check
- `/api/status`: Detailed status including:
  - Recent articles count
  - Scraping success rate
  - Active scrapers
  - Error logs

## Development Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables
4. Run the application:
   ```bash
   python app.py
   ```

## Testing

Run tests using:
```bash
python -m pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## License

This project is proprietary and confidential. 