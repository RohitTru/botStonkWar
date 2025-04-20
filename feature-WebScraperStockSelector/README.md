# Stock Scraper System

## Overview
This microservice is responsible for discovering and collecting stock-related information from various sources across the web. It serves as the initial data collection point in our stock trading bot system.

## Architecture

### Components
1. **Web Scraper**
   - Base scraper class (`app/scrapers/base.py`)
   - Source-specific scrapers (Yahoo Finance, Seeking Alpha, etc.)
   - Article content extraction and processing

2. **Database**
   - MySQL database for persistent storage
   - Tables for stocks, articles, and analysis data
   - Efficient indexing for quick lookups

3. **API & Dashboard**
   - Flask-based REST API
   - Real-time monitoring dashboard
   - Health check endpoints

4. **Services**
   - Stock service for managing stock data
   - Article service for managing article data
   - Logging service for system monitoring

### Data Flow
1. Scrapers continuously monitor sources for new articles
2. Articles are processed and stock symbols are extracted
3. Data is stored in the database
4. Dashboard displays real-time statistics
5. Other services can access the data via API

## Development Guide

### Adding New Scrapers
1. Create a new file in `app/scrapers/` (e.g., `new_source.py`)
2. Inherit from `BaseScraper`
3. Implement the `get_articles` method
4. Add custom parsing logic if needed
5. Register the scraper in the main application

Example:
```python
from app.scrapers.base import BaseScraper

class NewSourceScraper(BaseScraper):
    def __init__(self):
        super().__init__('new_source')
        
    def get_articles(self):
        # Implement article fetching logic
        pass
```

### Database Schema
- `stocks`: Stock metadata
- `raw_articles`: Original article content
- `processed_articles`: Processed article content
- `sentiment_analysis`: Sentiment analysis results
- `technical_analysis`: Technical analysis data

### API Endpoints
- `GET /`: Dashboard
- `GET /api/status`: System status
- `GET /health`: Health check

### Environment Variables
- `MYSQL_HOST`: Database host
- `MYSQL_USER`: Database user
- `MYSQL_PASSWORD`: Database password
- `MYSQL_SCRAPING_DATABASE`: Database name
- `APP_PORT`: Application port

## Deployment

### Docker
The service is containerized and can be deployed using Docker:
```bash
docker build -t rohittru/bot-stonk-war:feature-WebScraperStockSelector .
docker push rohittru/bot-stonk-war:feature-WebScraperStockSelector
```

### CI/CD
The service is integrated with the CI/CD pipeline:
1. Code is pushed to the repository
2. GitHub Actions builds the Docker image
3. Image is pushed to Docker Hub
4. Watchtower updates the running container

## Monitoring
- Real-time dashboard at `http://feature-scraper-selector.emerginary.com`
- System logs in `logs/` directory
- Health checks every 30 seconds

## Scaling
The system is designed to be scalable:
1. Multiple scrapers can run simultaneously
2. Database is optimized for high read/write operations
3. Redis is used for caching and message queuing

## Future Enhancements
1. Add more data sources
2. Implement advanced stock symbol extraction
3. Add article categorization
4. Implement rate limiting
5. Add more detailed analytics

## Troubleshooting
1. Check logs in `logs/` directory
2. Verify database connection
3. Check scraper status in dashboard
4. Monitor system resources

## Contributing
1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Submit a pull request 