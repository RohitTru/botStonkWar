import threading
from concurrent.futures import ThreadPoolExecutor
import logging
from app.scrapers.yahoo_finance import YahooFinanceScraper

logger = logging.getLogger(__name__)

class ScraperManager:
    def __init__(self, max_workers=3):
        self.scrapers = []
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = False
        self.threads = []
        self.initialize_scrapers()
        
    def initialize_scrapers(self):
        """Initialize all scrapers."""
        # Add scrapers here
        self.scrapers.append(YahooFinanceScraper())
        logger.info(f"Initialized {len(self.scrapers)} scrapers")
        
    def start_scraper(self, scraper):
        """Run a single scraper."""
        logger.info(f"Starting scraper: {scraper.name}")
        scraper.run()
        
    def start(self):
        """Start all scrapers in separate threads."""
        if self.running:
            logger.warning("Scrapers are already running")
            return
            
        self.running = True
        logger.info("Starting all scrapers")
        
        # Submit each scraper to the thread pool
        for scraper in self.scrapers:
            future = self.executor.submit(self.start_scraper, scraper)
            self.threads.append(future)
            
    def stop(self):
        """Stop all scrapers."""
        if not self.running:
            logger.warning("Scrapers are not running")
            return
            
        self.running = False
        logger.info("Stopping all scrapers")
        
        # Shutdown the executor (will wait for running tasks to complete)
        self.executor.shutdown(wait=True)
        self.threads = []
        
    def get_status(self):
        """Get the status of all scrapers."""
        return {
            'running': self.running,
            'scraper_count': len(self.scrapers),
            'active_scrapers': [scraper.name for scraper in self.scrapers]
        } 