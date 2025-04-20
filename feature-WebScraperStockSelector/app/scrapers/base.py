from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from datetime import datetime
import time
import logging

class BaseScraper(ABC):
    def __init__(self, name):
        self.name = name
        self.logger = logging.getLogger(f"scraper.{name}")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    @abstractmethod
    def get_articles(self):
        """Get articles from the source. Must be implemented by child classes."""
        pass

    def fetch_article_content(self, url):
        """Fetch and parse article content using newspaper3k."""
        try:
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
        while True:
            try:
                self.logger.info(f"Starting {self.name} scraper run")
                articles = self.get_articles()
                self.logger.info(f"Found {len(articles)} articles")
                
                for article in articles:
                    # Process each article
                    self.process_article(article)
                
                self.logger.info(f"Completed {self.name} scraper run")
                
            except Exception as e:
                self.logger.error(f"Error in {self.name} scraper: {str(e)}")
            
            # Sleep for a while before next run
            time.sleep(300)  # 5 minutes

    def process_article(self, article_data):
        """Process a single article."""
        try:
            # Fetch full article content
            content = self.fetch_article_content(article_data['url'])
            if not content:
                return

            # Extract stock symbols
            stock_symbols = self.extract_stock_symbols(content)
            if not stock_symbols:
                return

            # Process for each stock mentioned
            for symbol in stock_symbols:
                self.save_article(symbol, article_data, content)

        except Exception as e:
            self.logger.error(f"Error processing article {article_data.get('url')}: {str(e)}")

    def save_article(self, symbol, article_data, content):
        """Save article to database. To be implemented with actual database operations."""
        # This is a placeholder. You'll need to implement actual database operations
        self.logger.info(f"Saving article for {symbol}: {article_data.get('title')}") 