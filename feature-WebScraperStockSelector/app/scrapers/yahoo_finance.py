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
from app.ticker_validator.validator import TickerValidator
from config import Config
import re

logger = setup_logger()

class YahooFinanceScraper:
    def __init__(self, db=None):
        """Initialize the Yahoo Finance scraper.
        
        Args:
            db: Optional database instance. If not provided, creates a new one.
        """
        self.db = db if db is not None else Database()
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5  # Threshold for logging warning
        self.scraper_manager = None  # Will be set by ScraperManager
        self.ticker_validator = TickerValidator(self.db)  # Initialize validator
        
        # Comprehensive Yahoo Finance RSS feeds
        self.rss_feeds = [
            # Main feeds
            "https://finance.yahoo.com/news/rssindex",
            
            # Market indices
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC",  # S&P 500
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI",   # Dow Jones
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^IXIC",  # NASDAQ
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^RUT",   # Russell 2000
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^VIX",   # Volatility Index
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^TNX",   # 10-Year Treasury Yield
            
            # Category feeds
            "https://finance.yahoo.com/rss/topstories",      # Top Stories
            "https://finance.yahoo.com/rss/stocks",          # Stocks
            "https://finance.yahoo.com/rss/bonds",           # Bonds
            "https://finance.yahoo.com/rss/industry-news",   # Industry News
            "https://finance.yahoo.com/rss/earnings",        # Earnings News
            "https://finance.yahoo.com/rss/mergers",         # Merger News
            "https://finance.yahoo.com/rss/personal-finance", # Personal Finance
            "https://finance.yahoo.com/rss/options",         # Options News
            "https://finance.yahoo.com/rss/dividends",       # Dividend News
            "https://finance.yahoo.com/rss/ipo",             # IPO News
            "https://finance.yahoo.com/rss/commodities",     # Commodities
            "https://finance.yahoo.com/rss/currencies",      # Forex News
            "https://finance.yahoo.com/rss/crypto",          # Cryptocurrency
            
            # Sector feeds
            "https://finance.yahoo.com/rss/sector-technology",
            "https://finance.yahoo.com/rss/sector-financial",
            "https://finance.yahoo.com/rss/sector-healthcare",
            "https://finance.yahoo.com/rss/sector-energy",
            "https://finance.yahoo.com/rss/sector-consumer-cyclical",
            "https://finance.yahoo.com/rss/sector-consumer-defensive",
            "https://finance.yahoo.com/rss/sector-industrial",
            "https://finance.yahoo.com/rss/sector-basic-materials",
            "https://finance.yahoo.com/rss/sector-real-estate",
            "https://finance.yahoo.com/rss/sector-utilities",
            "https://finance.yahoo.com/rss/sector-communication-services",
            
            # Popular stock feeds (Top companies by market cap and high-interest stocks)
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AAPL",   # Apple
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=MSFT",   # Microsoft
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GOOGL",  # Google
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=AMZN",   # Amazon
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=META",   # Meta
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=NVDA",   # NVIDIA
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=TSLA",   # Tesla
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=BRK-B",  # Berkshire Hathaway
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=JPM",    # JPMorgan Chase
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=V",      # Visa
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=JNJ",    # Johnson & Johnson
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=WMT",    # Walmart
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=PG",     # Procter & Gamble
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=MA",     # Mastercard
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=HD",     # Home Depot
            
            # ETF feeds (Major ETFs that indicate market trends)
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=SPY",    # S&P 500 ETF
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=QQQ",    # Nasdaq ETF
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=IWM",    # Russell 2000 ETF
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=DIA",    # Dow Jones ETF
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GLD",    # Gold ETF
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=XLF",    # Financial Sector ETF
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=XLK",    # Technology Sector ETF
            
            # Market indicators
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=CL=F",   # Crude Oil Futures
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F",   # Gold Futures
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=SI=F",   # Silver Futures
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=EURUSD=X", # EUR/USD
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=USDJPY=X", # USD/JPY
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=BTC-USD",  # Bitcoin
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=ETH-USD",  # Ethereum
            
            # Market movers and analysis
            "https://finance.yahoo.com/rss/marketmovers",
            "https://finance.yahoo.com/rss/gainers",
            "https://finance.yahoo.com/rss/losers",
            "https://finance.yahoo.com/rss/mostactives",
            "https://finance.yahoo.com/rss/undervalued",
            "https://finance.yahoo.com/rss/growth",
            "https://finance.yahoo.com/rss/value",
            "https://finance.yahoo.com/rss/analysts",        # Analyst Coverage
            "https://finance.yahoo.com/rss/research"         # Market Research
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def set_manager(self, manager):
        """Set the scraper manager instance."""
        self.scraper_manager = manager

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
                logger.info(f"Article already exists in database: {url}")
                self.consecutive_failures = 0  # Reset on successful check
                # Log duplicate as warning status
                self.db.add_scraping_log(
                    status='DUPLICATE',
                    source_type='yahoo_finance',
                    url=url,
                    error_message='Article already exists in database'
                )
                return

            # Get article details first before logging start
            article_data = self.scrape_article(url, entry)
            if not article_data:
                self.consecutive_failures += 1
                if self.consecutive_failures >= self.max_consecutive_failures:
                    logger.warning(f"High number of consecutive failures ({self.consecutive_failures}), but continuing...")
                # Log failed scrape as error
                self.db.add_scraping_log(
                    status='ERROR',
                    source_type='yahoo_finance',
                    url=url,
                    error_message='Failed to scrape article content'
                )
                return
            
            # Add missing fields to article data
            article_data.update({
                'link': url,
                'source': 'Yahoo Finance',
                'published_date': datetime.strptime(
                    entry.get('published', datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')),
                    '%a, %d %b %Y %H:%M:%S %z'
                ) if entry.get('published') else datetime.now(timezone.utc),
                'scraped_date': datetime.now(timezone.utc)
            })
            
            # Store the article
            try:
                article_id = self.db.add_article(article_data)
                logger.info(f"Successfully stored article {url} with ID {article_id}")
                
                # Log successful scrape
                self.db.add_scraping_log(
                    status='SUCCESS',
                    source_type='yahoo_finance',
                    url=url
                )
                
                # Reset failure counter on successful scrape
                self.consecutive_failures = 0
                
            except Exception as e:
                logger.error(f"Failed to store article {url}: {str(e)}")
                self.db.add_scraping_log(
                    status='ERROR',
                    source_type='yahoo_finance',
                    url=url,
                    error_message=f"Storage error: {str(e)}"
                )
                raise
            
        except Exception as e:
            logger.error(f"Error processing article {url}: {str(e)}")
            logger.error(traceback.format_exc())
            self.db.add_scraping_log(
                status='ERROR',
                source_type='yahoo_finance',
                url=url,
                error_message=str(e)
            )

    def scrape_article(self, url, entry=None):
        """Scrape article content and extract stock symbols."""
        try:
            logger.info(f"Attempting to scrape article: {url}")
            response = requests.get(url, headers=self.headers, timeout=10)
            logger.info(f"Article response status: {response.status_code}")
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Improved title extraction - prioritize RSS feed title
            title = None
            if entry and 'title' in entry:
                title = entry['title']
                # Clean up the title if it contains "Yahoo Finance"
                if "Yahoo Finance" in title:
                    # Try to extract the actual article title from the URL
                    url_parts = url.split('/')
                    if len(url_parts) > 0:
                        last_part = url_parts[-1]
                        # Remove query parameters and file extension
                        last_part = last_part.split('?')[0].split('.')[0]
                        # Replace hyphens with spaces and capitalize
                        title = ' '.join(word.capitalize() for word in last_part.split('-'))
            
            # Fallback to meta og:title
            if not title:
                meta_title = soup.find('meta', property='og:title')
                if meta_title and meta_title.get('content'):
                    title = meta_title['content']
            
            # Fallback to h1 tag
            if not title:
                h1_tag = soup.find('h1')
                if h1_tag and h1_tag.get_text(strip=True):
                    title = h1_tag.get_text(strip=True)
            
            title = title or 'Untitled Article'

            # Improved content extraction with more selectors
            content = None
            content_selectors = [
                'div[class*="caas-body"]',
                'div[class*="article-body"]',
                'div[class*="content"]',
                'article',
                'div[class*="story-body"]',
                'div[class*="article-content"]',
                'div[class*="post-content"]',
                'div[class*="entry-content"]',
                'div[class*="main-content"]',
                'div[class*="story-content"]',
                'div[class*="article-text"]',
                'div[class*="post-body"]',
                'div[class*="entry-body"]',
                'div[class*="main-body"]',
                'div[class*="story-text"]',
                'div[class*="article-main"]',
                'div[class*="post-main"]',
                'div[class*="entry-main"]',
                'div[class*="main-article"]',
                'div[class*="story-main"]'
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    # Get all text content, including nested elements
                    content = ' '.join([p.get_text(strip=True) for p in content_div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])])
                    if content and len(content) > 100:  # Ensure we have substantial content
                        break
            
            if not content or len(content) < 100:
                logger.warning(f"No substantial content found for article: {url}")
                return None

            article_data = {
                'title': title,
                'content': content,
                'link': url,
                'source': 'Yahoo Finance',
                'published_date': datetime.now(timezone.utc),
                'scraped_date': datetime.now(timezone.utc)
            }

            # Extract and validate symbols using the new validator logic
            all_symbols, validated_symbols = self.ticker_validator.process_article_symbols(article_data)
            article_data['symbols'] = all_symbols
            article_data['validated_symbols'] = validated_symbols

            logger.info(f"Successfully scraped article: {url}")
            logger.info(f"Content length: {len(content)}")
            logger.info(f"Found symbols: {all_symbols}")
            logger.info(f"Validated symbols: {validated_symbols}")
            return article_data
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error scraping article {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def get_articles_to_scrape(self):
        """Get a list of articles to scrape from RSS feeds."""
        articles = []
        try:
            for feed_url in self.rss_feeds:
                try:
                    feed = feedparser.parse(feed_url)
                    if hasattr(feed, 'bozo_exception'):
                        logger.error(f"Feed parsing error: {str(feed.bozo_exception)}")
                        continue
                    
                    if not feed.entries:
                        continue
                    
                    for entry in feed.entries:
                        url = entry.get('link')
                        if not url:
                            continue
                            
                        # Check if article already exists
                        if not self.db.get_article_by_url(url):
                            articles.append({
                                'url': url,
                                'title': entry.get('title', ''),
                                'published': entry.get('published')
                            })
                            
                except Exception as e:
                    logger.error(f"Error processing feed {feed_url}: {str(e)}")
                    continue
                    
            return articles
            
        except Exception as e:
            logger.error(f"Error getting articles to scrape: {str(e)}")
            return []

    def run(self):
        """Run the scraper continuously."""
        logger.info("Starting Yahoo Finance scraper...")
        
        # Get scraping interval from config
        scrape_interval = Config.SCRAPE_INTERVAL
        
        # Run immediately on startup
        logger.info("Starting initial scrape...")
        try:
            self.scrape_feed()
        except Exception as e:
            logger.error(f"Initial scrape failed: {str(e)}")
            logger.error(traceback.format_exc())
        
        while True:
            try:
                logger.info(f"Waiting {scrape_interval} seconds for next scrape cycle...")
                time.sleep(scrape_interval)
                
                # Check if scraper is paused
                if self.scraper_manager and self.scraper_manager.is_paused('yahoo_finance'):
                    logger.info("Scraper is paused, skipping cycle")
                    continue
                
                # Run scrape cycle with retry logic
                max_retries = 3
                retry_delay = 60  # 1 minute
                
                for attempt in range(max_retries):
                    try:
                        self.scrape_feed()
                        break  # Success, exit retry loop
                    except Exception as e:
                        logger.error(f"Scrape cycle failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        logger.error(traceback.format_exc())
                        
                        if attempt < max_retries - 1:  # Don't sleep on last attempt
                            time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                        
            except Exception as e:
                logger.error(f"Error in scraper run loop: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(60)  # Wait 1 minute on error before retrying 