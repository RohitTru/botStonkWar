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
from app.ticker_validator import TickerValidator

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
            
            # Parse published date
            published_date = None
            if 'published' in entry:
                try:
                    published_date = datetime.strptime(entry.get('published'), '%Y-%m-%dT%H:%M:%SZ')
                except ValueError:
                    try:
                        published_date = datetime.strptime(entry.get('published'), '%a, %d %b %Y %H:%M:%S %z')
                    except ValueError:
                        logger.warning(f"Could not parse published date: {entry.get('published')}")
                        published_date = datetime.now(timezone.utc)

            # Get all scraped symbols
            raw_symbols = article_data.get('symbols', [])
            
            # Validate symbols
            validated_symbols = []
            if raw_symbols:
                # Create validation context
                validation_context = {
                    'title': article_data['title'],
                    'content': article_data['content']
                }
                
                # Validate each symbol
                for symbol in raw_symbols:
                    try:
                        # Basic validation first
                        if len(symbol) <= 5 and symbol.isalpha():
                            # Check if symbol exists in our database
                            if self.ticker_validator.validate_ticker(symbol):
                                validated_symbols.append(symbol)
                    except Exception as e:
                        logger.warning(f"Error validating symbol {symbol}: {str(e)}")
                        continue

            # Prepare article data for database
            article_data.update({
                'title': entry.get('title', ''),
                'link': url,
                'source': 'yahoo_finance',
                'published_date': published_date,
                'scraped_date': datetime.now(timezone.utc),
                'symbols': raw_symbols,  # Store all found symbols
                'validated_symbols': validated_symbols  # Store only validated symbols
            })

            # Add to database
            if not self.db.add_article(article_data):
                raise Exception("Failed to save article to database")

            # Log success
            log_data = {
                'timestamp': datetime.now(timezone.utc),
                'status': 'SUCCESS',
                'source_type': 'yahoo_finance',
                'url': url
            }
            self.db.add_scraping_log(log_data)
            
            logger.info(f"Successfully processed article: {url}")
            logger.info(f"Found {len(raw_symbols)} symbols, {len(validated_symbols)} validated")
            
        except Exception as e:
            logger.error(f"Error processing article {url}: {str(e)}")
            
            # Log failure
            log_data = {
                'timestamp': datetime.now(timezone.utc),
                'status': 'FAILED',
                'source_type': 'yahoo_finance',
                'url': url,
                'error_message': str(e)
            }
            self.db.add_scraping_log(log_data)
            
            return False
        
        return True

    def scrape_article(self, url):
        """Scrape article content and extract stock symbols."""
        try:
            logger.info(f"Attempting to scrape article: {url}")
            
            # Make request with headers
            response = requests.get(url, headers=self.headers, timeout=10)
            logger.info(f"Article response status: {response.status_code}")
            
            # Check response
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract title
            title = None
            h1_tag = soup.find('h1')
            if h1_tag:
                title = h1_tag.get_text().strip()
            
            # Try different content selectors
            content = None
            content_selectors = [
                'div[class*="caas-body"]',  # Yahoo Finance
                'div[class*="article-body"]',  # Generic
                'div[class*="content"]',  # Generic
                'article',  # Very generic
            ]
            
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    content = content_div.get_text().strip()
                    break
            
            if not content:
                logger.warning(f"No content found with any selector for article: {url}")
                return None
            
            # Extract stock symbols using multiple methods
            symbols = set()
            
            # Method 1: Extract from quote links
            quote_links = soup.find_all('a', href=lambda x: x and '/quote/' in x)
            for link in quote_links:
                symbol = link.get_text().strip().upper()
                if symbol and len(symbol) <= 5:  # Basic symbol validation
                    symbols.add(symbol)
            
            # Method 2: Extract from spans with symbol class
            symbol_spans = soup.find_all('span', class_=lambda x: x and 'symbol' in x.lower())
            for span in symbol_spans:
                symbol = span.get_text().strip().upper()
                if symbol and len(symbol) <= 5:
                    symbols.add(symbol)
            
            # Method 3: Use regex to find common stock symbol formats
            import re
            # Match patterns like (AAPL), $AAPL, NYSE:AAPL, NASDAQ:AAPL
            symbol_patterns = [
                r'\(([A-Z]{1,5})\)',  # (AAPL)
                r'\$([A-Z]{1,5})\b',  # $AAPL
                r'(?:NYSE|NASDAQ):\s*([A-Z]{1,5})\b',  # NYSE:AAPL or NASDAQ:AAPL
                r'\b[A-Z]{1,5}\b'  # AAPL (basic symbol format)
            ]
            
            for pattern in symbol_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    symbol = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    if symbol and len(symbol) <= 5:
                        symbols.add(symbol)
            
            # Convert symbols to list and sort
            symbols_list = sorted(list(symbols))
            
            logger.info(f"Successfully scraped article: {url}")
            logger.info(f"Content length: {len(content)}")
            logger.info(f"Found symbols: {symbols_list}")
            
            return {
                'title': title or 'Untitled Article',
                'content': content,
                'symbols': symbols_list
            }
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            return None

    def run(self):
        """Run the scraper continuously."""
        logger.info("Starting Yahoo Finance scraper...")
        
        # Run immediately on startup
        logger.info("Starting initial scrape...")
        self.scrape_feed()
        
        while True:
            try:
                logger.info("Waiting for next scrape cycle...")
                time.sleep(60)  # Wait 60 seconds between cycles
                
                # Double check pause state before starting new cycle
                self.scrape_feed()
                    
            except Exception as e:
                logger.error(f"Error in scraper run loop: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(10)  # Wait 10 seconds on error before retrying 