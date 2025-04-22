import feedparser
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time
import random
import sys
import traceback
from app.utils.logging import setup_logger
from app.database import Database

logger = setup_logger()

class YahooFinanceScraper:
    def __init__(self):
        self.seen_urls = set()
        self.db = Database()
        # Updated RSS feed URLs
        self.rss_feeds = [
            "https://finance.yahoo.com/news/rssindex",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI"
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

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
            logger.info(f"Article response content (first 500 chars): {response.text[:500]}")
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content
            content_div = soup.find('div', {'class': 'caas-body'})
            if not content_div:
                logger.warning(f"No content found for article: {url}")
                # Try alternative content selectors
                content_div = soup.find('div', {'class': 'canvas-body'}) or \
                            soup.find('div', {'class': 'article-body'}) or \
                            soup.find('article')
                
                if not content_div:
                    logger.error(f"No content found with any selector for article: {url}")
                    logger.error(f"Page structure: {soup.prettify()[:1000]}")
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
            
            logger.info(f"Successfully scraped article: {url}")
            logger.info(f"Content length: {len(content)}")
            logger.info(f"Found symbols: {symbols}")
            
            return {
                'content': content,
                'symbols': list(set(symbols))  # Remove duplicates
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
                        try:
                            # Debug entry data
                            logger.info(f"Processing entry - Title: {entry.get('title', 'No title')}")
                            logger.info(f"Entry link: {entry.get('link', 'No link')}")
                            logger.info(f"Entry published: {entry.get('published', 'No date')}")
                            
                            url = entry.get('link')
                            if not url:
                                logger.error("Entry has no URL, skipping")
                                continue
                            
                            # Skip if already seen
                            if url in self.seen_urls:
                                logger.debug(f"Skipping already seen article: {url}")
                                continue
                            
                            self.seen_urls.add(url)
                            
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
            # Log start of scraping
            log_data = {
                'timestamp': datetime.now(),
                'status': 'STARTED',
                'source_type': 'yahoo_finance',
                'url': url
            }
            self.db.add_scraping_log(log_data)
            
            # Get article details
            article_data = self.scrape_article(url)
            if not article_data:
                raise Exception("Failed to scrape article content")
            
            # Prepare article data
            article = {
                'title': entry.get('title', ''),
                'link': url,
                'content': article_data['content'],
                'symbols': article_data['symbols'],
                'source': 'yahoo_finance',
                'published_date': datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now(),
                'scraped_date': datetime.now()
            }
            
            # Save to database
            if self.db.add_article(article):
                log_data = {
                    'timestamp': datetime.now(),
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
                'timestamp': datetime.now(),
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
                logger.info("Waiting for next scrape cycle...")
                time.sleep(60)
                logger.info("Starting new scrape cycle...")
                self.scrape_feed()
            except Exception as e:
                logger.error(f"Error in scraper run loop: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(10)  # Wait 10 seconds on error before retrying 