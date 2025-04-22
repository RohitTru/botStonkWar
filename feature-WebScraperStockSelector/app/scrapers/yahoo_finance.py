import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import random
from app.utils.logging import setup_logger
from app.database import Database

logger = setup_logger()

class YahooFinanceScraper:
    def __init__(self):
        self.seen_urls = set()
        self.db = Database()
        self.base_url = "https://finance.yahoo.com/rss"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def scrape_article(self, url):
        """Scrape a single article from Yahoo Finance."""
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content
            content_div = soup.find('div', {'class': 'caas-body'})
            if not content_div:
                logger.warning(f"No content found for article: {url}")
                return None
                
            content = content_div.get_text(strip=True)
            
            # Extract stock symbols
            symbols = []
            symbol_tags = soup.find_all('a', {'class': 'caas-link'})
            for tag in symbol_tags:
                href = tag.get('href', '')
                if '/quote/' in href:
                    symbol = href.split('/quote/')[1].split('?')[0]
                    symbols.append(symbol)
            
            return {
                'content': content,
                'symbols': list(set(symbols))  # Remove duplicates
            }
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {e}")
            return None

    def scrape_feed(self):
        """Scrape articles from Yahoo Finance RSS feed."""
        try:
            feed = feedparser.parse(self.base_url)
            
            for entry in feed.entries:
                url = entry.link
                
                # Skip if already seen
                if url in self.seen_urls:
                    continue
                    
                self.seen_urls.add(url)
                
                # Log start of scraping
                log_data = {
                    'timestamp': datetime.now(),
                    'status': 'STARTED',
                    'source_type': 'yahoo_finance',
                    'url': url
                }
                self.db.add_scraping_log(log_data)
                
                try:
                    # Get article details
                    article_data = self.scrape_article(url)
                    if not article_data:
                        raise Exception("Failed to scrape article content")
                    
                    # Prepare article data
                    article = {
                        'title': entry.title,
                        'link': url,
                        'content': article_data['content'],
                        'symbols': article_data['symbols'],
                        'source': 'yahoo_finance',
                        'published_date': datetime(*entry.published_parsed[:6]),
                        'scraped_date': datetime.now()
                    }
                    
                    # Save to database
                    if self.db.add_article(article):
                        # Log success
                        log_data = {
                            'timestamp': datetime.now(),
                            'status': 'SUCCESS',
                            'source_type': 'yahoo_finance',
                            'url': url
                        }
                        self.db.add_scraping_log(log_data)
                        logger.info(f"Successfully scraped article: {url}")
                    else:
                        raise Exception("Failed to save article to database")
                        
                except Exception as e:
                    # Log failure
                    log_data = {
                        'timestamp': datetime.now(),
                        'status': 'FAILED',
                        'source_type': 'yahoo_finance',
                        'url': url,
                        'error_message': str(e)
                    }
                    self.db.add_scraping_log(log_data)
                    logger.error(f"Error processing article {url}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error scraping Yahoo Finance feed: {e}")
            # Log feed-level failure
            log_data = {
                'timestamp': datetime.now(),
                'status': 'FAILED',
                'source_type': 'yahoo_finance',
                'url': self.base_url,
                'error_message': str(e)
            }
            self.db.add_scraping_log(log_data)

    def run(self):
        """Run the scraper continuously."""
        logger.info("Starting Yahoo Finance scraper...")
        # Run immediately on startup
        self.scrape_feed()
        
        while True:
            try:
                # Wait 1 minute before next scrape
                time.sleep(60)
                self.scrape_feed()
            except Exception as e:
                logger.error(f"Error in scraper run loop: {e}")
                time.sleep(10)  # Wait 10 seconds on error before retrying 