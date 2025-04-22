import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import time
import random
import sys
import traceback
from app.utils.logging import setup_logger
from app.database import Database
import pytz

logger = setup_logger()

class YahooFinanceScraper:
    def __init__(self):
        self.db = Database()
        self._paused = False  # Make pause state private
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5  # Threshold for logging warning
        # Updated RSS feed URLs
        self.rss_feeds = [
            "https://finance.yahoo.com/news/rssindex",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    @property
    def paused(self):
        """Get the current pause state."""
        return self._paused

    @paused.setter
    def paused(self, value):
        """Set the pause state with logging."""
        if self._paused != value:
            self._paused = value
            logger.info(f"Scraper {'paused' if value else 'resumed'} explicitly")

    def _check_pause_state(self):
        """Check if scraper is paused and log if it is."""
        if self._paused:
            logger.debug("Scraper is currently paused")
            return True
        return False

    def test_feed_access(self):
        """Test access to RSS feeds"""
        logger.info("Testing RSS feed access...")
        for feed_url in self.rss_feeds:
            try:
                logger.info(f"Testing feed URL: {feed_url}")
                response = requests.get(feed_url, headers=self.headers)
                response.raise_for_status()
                logger.info(f"Feed response status: {response.status_code}")
                logger.info(f"Feed response content (first 500 chars): {response.text[:500]}")
                
                feed = feedparser.parse(feed_url)
                logger.info(f"Feed parsing result - version: {feed.version}, entries: {len(feed.entries)}")
                
                if len(feed.entries) > 0:
                    sample_entry = feed.entries[0]
                    logger.info(f"Sample entry - Title: {sample_entry.get('title', 'No title')}")
                    logger.info(f"Sample entry - Link: {sample_entry.get('link', 'No link')}")
            except Exception as e:
                logger.error(f"Error testing feed {feed_url}: {str(e)}")
                logger.error(traceback.format_exc())

    def scrape_article(self, url):
        """Scrape a single article from Yahoo Finance."""
        try:
            # Add random delay to avoid rate limiting
            time.sleep(random.uniform(1, 3))
            
            logger.info(f"Attempting to scrape article: {url}")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            logger.info(f"Article response status: {response.status_code}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content
            content_div = soup.find('div', {'class': 'caas-body'})
            if not content_div:
                logger.warning(f"No content found with caas-body for article: {url}")
                # Try alternative content selectors
                content_div = soup.find('div', {'class': 'canvas-body'}) or \
                            soup.find('div', {'class': 'article-body'}) or \
                            soup.find('article')
                
                if not content_div:
                    logger.error(f"No content found with any selector for article: {url}")
                    return None
            
            content = content_div.get_text(strip=True)
            
            # Extract stock symbols - try multiple methods
            symbols = set()
            
            # Method 1: Look for quote links
            quote_links = soup.find_all('a', href=lambda x: x and '/quote/' in x)
            for link in quote_links:
                href = link.get('href', '')
                if '/quote/' in href:
                    symbol = href.split('/quote/')[1].split('?')[0].split('/')[0]
                    if symbol and len(symbol) < 10:  # Basic validation
                        symbols.add(symbol)
            
            # Method 2: Look for symbol spans
            symbol_spans = soup.find_all('span', {'class': ['Fw(b)', 'ticker']})
            for span in symbol_spans:
                symbol = span.get_text(strip=True)
                if symbol and len(symbol) < 10:
                    symbols.add(symbol)
            
            # Method 3: Look for common stock symbol patterns in content
            if content:
                # Look for patterns like (TICKER) or $TICKER
                import re
                pattern = r'[\(\s]([A-Z]{1,5})[\)\s]|\$([A-Z]{1,5})'
                matches = re.finditer(pattern, content)
                for match in matches:
                    symbol = match.group(1) or match.group(2)
                    if symbol and len(symbol) < 6:
                        symbols.add(symbol)
            
            symbols = list(symbols)
            logger.info(f"Successfully scraped article: {url}")
            logger.info(f"Content length: {len(content)}")
            logger.info(f"Found symbols: {symbols}")
            
            return {
                'content': content,
                'symbols': symbols
            }
            
        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            logger.error(traceback.format_exc())
            return None
    
    def scrape_feed(self):
        """Scrape articles from Yahoo Finance RSS feeds."""
        try:
            logger.info("Starting feed scraping cycle...")
            for feed_url in self.rss_feeds:
                # Check pause state before processing each feed
                if self._check_pause_state():
                    return
                    
                try:
                    logger.info(f"Fetching RSS feed: {feed_url}")
                    feed = feedparser.parse(feed_url)
                    
                    # Debug feed parsing
                    logger.info(f"Feed parsing complete - Status: {feed.get('status', 'No status')}")
                    logger.info(f"Feed version: {feed.get('version', 'No version')}")
                    logger.info(f"Feed bozo: {feed.get('bozo', 0)}")
                    logger.info(f"Feed headers: {feed.get('headers', {})}")
                    
                    if hasattr(feed, 'bozo_exception'):
                        logger.error(f"Feed parsing error: {str(feed.bozo_exception)}")
                        continue
                    
                    if not feed.entries:
                        logger.warning(f"No entries found in feed: {feed_url}")
                        continue
                    
                    logger.info(f"Processing {len(feed.entries)} articles from feed: {feed_url}")
                    
                    for entry in feed.entries:
                        # Check pause state before processing each article
                        if self._check_pause_state():
                            return
                            
                        try:
                            # Debug entry data
                            logger.info(f"Processing entry - Title: {entry.get('title', 'No title')}")
                            logger.info(f"Entry link: {entry.get('link', 'No link')}")
                            logger.info(f"Entry published: {entry.get('published', 'No date')}")
                            
                            url = entry.get('link')
                            if not url:
                                logger.error("Entry has no URL, skipping")
                                continue
                            
                            # Process the article
                            self._process_article(entry)
                            
                        except Exception as e:
                            logger.error(f"Error processing feed entry: {str(e)}")
                            logger.error(traceback.format_exc())
                            continue
                            
                except Exception as e:
                    logger.error(f"Error processing feed {feed_url}: {str(e)}")
                    logger.error(traceback.format_exc())
                    continue
                    
        except Exception as e:
            logger.error(f"Error in feed scraping cycle: {str(e)}")
            logger.error(traceback.format_exc())

    def _process_article(self, entry):
        """Process a single article entry."""
        url = entry.get('link')
        try:
            # Check if article already exists in database
            existing_article = self.db.get_article_by_url(url)
            if existing_article:
                logger.debug(f"Article already exists in database: {url}")
                self.consecutive_failures = 0  # Reset on successful check
                return

            # Get article details first before logging start
            article_data = self.scrape_article(url)
            if not article_data:
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.max_consecutive_failures:
                    logger.warning(f"High number of consecutive failures ({self.consecutive_failures}), but continuing...")
                raise Exception("Failed to scrape article content")
            
            # Reset failure counter on successful scrape
            self.consecutive_failures = 0
            
            # Only log STARTED if we successfully got the article content
            log_data = {
                'timestamp': datetime.now(timezone.utc),
                'status': 'STARTED',
                'source_type': 'yahoo_finance',
                'url': url
            }
            self.db.add_scraping_log(log_data)
            
            # Convert published date to UTC
            if hasattr(entry, 'published_parsed'):
                published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            else:
                published_date = datetime.now(timezone.utc)
            
            # Prepare article data
            article = {
                'title': entry.get('title', ''),
                'link': url,
                'content': article_data['content'],
                'symbols': article_data['symbols'],
                'source': 'yahoo_finance',
                'published_date': published_date,
                'scraped_date': datetime.now(timezone.utc)
            }
            
            # Save to database
            if self.db.add_article(article):
                log_data = {
                    'timestamp': datetime.now(timezone.utc),
                    'status': 'SUCCESS',
                    'source_type': 'yahoo_finance',
                    'url': url
                }
                self.db.add_scraping_log(log_data)
                logger.info(f"Successfully saved article: {url}")
            else:
                raise Exception("Failed to save article to database")
            
        except Exception as e:
            log_data = {
                'timestamp': datetime.now(timezone.utc),
                'status': 'FAILED',
                'source_type': 'yahoo_finance',
                'url': url,
                'error_message': str(e)
            }
            self.db.add_scraping_log(log_data)
            logger.error(f"Error processing article {url}: {str(e)}")
            logger.error(traceback.format_exc())

    def run(self):
        """Run the scraper continuously."""
        logger.info("Starting Yahoo Finance scraper...")
        
        # Test feed access first
        self.test_feed_access()
        
        # Run immediately on startup
        logger.info("Starting initial scrape...")
        self.scrape_feed()
        
        while True:
            try:
                # Check if paused
                if self._check_pause_state():
                    time.sleep(5)
                    continue
                
                logger.info("Waiting for next scrape cycle...")
                time.sleep(60)  # Wait 60 seconds between cycles
                
                # Double check pause state before starting new cycle
                if not self._check_pause_state():
                    logger.info("Starting new scrape cycle...")
                    self.scrape_feed()
                    
            except Exception as e:
                logger.error(f"Error in scraper run loop: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(10)  # Wait 10 seconds on error before retrying 