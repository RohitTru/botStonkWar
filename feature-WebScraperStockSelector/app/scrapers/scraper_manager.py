import threading
from app.scrapers.yahoo_finance import YahooFinanceScraper
from app.utils.logging import setup_logger

logger = setup_logger()

class ScraperManager:
    def __init__(self):
        """Initialize the scraper manager."""
        self.yahoo_finance_scraper = None
        self.scraper_thread = None
        self.running = False
        logger.info("Scraper manager initialized")

    def start(self):
        """Start the scraping process."""
        if self.running:
            logger.warning("Scraper is already running")
            return False

        try:
            self.yahoo_finance_scraper = YahooFinanceScraper()
            self.scraper_thread = threading.Thread(target=self.yahoo_finance_scraper.run)
            self.scraper_thread.daemon = True
            self.scraper_thread.start()
            self.running = True
            logger.info("Scraper started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting scraper: {e}")
            return False

    def stop(self):
        """Stop the scraping process."""
        if not self.running:
            logger.warning("Scraper is not running")
            return False

        try:
            self.running = False
            if self.yahoo_finance_scraper:
                self.yahoo_finance_scraper = None
            if self.scraper_thread:
                self.scraper_thread = None
            logger.info("Scraper stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Error stopping scraper: {e}")
            return False

    def get_status(self):
        """Get the current status of the scraper."""
        return {
            'running': self.running,
            'active_scrapers': ['yahoo_finance'] if self.running else []
        } 