from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from datetime import datetime
import time
import logging
from app import db
from app.services.stock_service import StockService
from app.services.article_service import ArticleService

class BaseScraper(ABC):
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(f"scraper.{name}")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.stock_service = StockService()
        self.article_service = ArticleService()

    @abstractmethod
    def get_articles(self):
        """Get articles from the source. Must be implemented by child classes."""
        pass

    def fetch_article_content(self, url):
        """Fetch and parse article content using newspaper3k."""
        try:
            self.logger.info(f"Fetching article content from {url}")
            article = Article(url)
            article.download()
            article.parse()
            return article.text
        except Exception as e:
            self.logger.error(f"Error fetching article {url}: {str(e)}")
            return None

    def extract_stock_symbols(self, text):
        """Extract stock symbols from text. This is a basic implementation."""
        # This is a placeholder. You might want to use a more sophisticated
        # method to extract stock symbols, possibly using regex or NLP.
        return []

    def run(self):
        """Main scraper loop."""
        self.logger.info(f"Starting {self.name} scraper")
        while True:
            try:
                self.logger.info(f"Starting {self.name} scraper run")
                articles = self.get_articles()
                self.logger.info(f"Found {len(articles)} articles")
                
                for article in articles:
                    try:
                        # Process each article
                        self.logger.info(f"Processing article: {article.get('title', 'No title')}")
                        self.process_article(article)
                    except Exception as e:
                        self.logger.error(f"Error processing article: {str(e)}")
                        continue
                
                self.logger.info(f"Completed {self.name} scraper run")
                
            except Exception as e:
                self.logger.error(f"Error in {self.name} scraper: {str(e)}")
            
            # Sleep for a while before next run
            sleep_time = 300  # 5 minutes
            self.logger.info(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)

    def process_article(self, article_data):
        """Process a single article."""
        try:
            self.logger.info(f"Processing article: {article_data.get('title')}")
            
            # Fetch full article content
            content = self.fetch_article_content(article_data['url'])
            if not content:
                self.logger.warning(f"No content found for article: {article_data.get('title')}")
                return

            # Extract stock symbols
            stock_symbols = self.extract_stock_symbols(content)
            self.logger.info(f"Found stock symbols: {stock_symbols}")
            
            if not stock_symbols:
                self.logger.info("No stock symbols found in article")
                return

            # Process for each stock mentioned
            for symbol in stock_symbols:
                try:
                    self.save_article(symbol, article_data, content)
                except Exception as e:
                    self.logger.error(f"Error saving article for symbol {symbol}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Error processing article {article_data.get('url')}: {str(e)}")

    def save_article(self, symbol, article_data, content):
        """Save article to database."""
        try:
            # Get or create stock
            stock = self.stock_service.get_or_create_stock(symbol)
            if not stock:
                self.logger.error(f"Could not get/create stock for symbol: {symbol}")
                return

            # Save the article
            self.article_service.save_raw_article(
                stock_id=stock.id,
                source=self.name,
                url=article_data['url'],
                title=article_data['title'],
                content=content,
                published_at=article_data.get('published_at')
            )
            self.logger.info(f"Saved article for stock {symbol}: {article_data.get('title')}")
            
        except Exception as e:
            self.logger.error(f"Error saving article for {symbol}: {str(e)}")
            # Make sure to rollback the session on error
            db.session.rollback() 