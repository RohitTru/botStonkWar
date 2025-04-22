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
        self.paused = False
        self.app = None
        logger.info("Scraper manager initialized")

    def init_app(self, app):
        """Initialize the scraper with Flask app context."""
        self.app = app
        logger.info("Scraper manager initialized with Flask app")
        return self

    def start(self):
        """Start the scraping process."""
        if self.running:
            logger.warning("Scraper is already running")
            return False

        try:
            self.yahoo_finance_scraper = YahooFinanceScraper()
            self.scraper_thread = threading.Thread(target=self.yahoo_finance_scraper.run)
            self.scraper_thread.daemon = True
            self.running = True
            self.paused = False
            self.scraper_thread.start()
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
            self.paused = False
            if self.yahoo_finance_scraper:
                self.yahoo_finance_scraper = None
            if self.scraper_thread:
                self.scraper_thread = None
            logger.info("Scraper stopped successfully")
            return True
        except Exception as e:
            logger.error(f"Error stopping scraper: {e}")
            return False

    def pause(self):
        """Pause the scraping process."""
        if not self.running:
            logger.warning("Scraper is not running")
            return False
        if self.paused:
            logger.warning("Scraper is already paused")
            return False

        try:
            self.paused = True
            if self.yahoo_finance_scraper:
                self.yahoo_finance_scraper.paused = True
            logger.info("Scraper paused successfully")
            return True
        except Exception as e:
            logger.error(f"Error pausing scraper: {e}")
            return False

    def resume(self):
        """Resume the scraping process."""
        if not self.running:
            logger.warning("Scraper is not running")
            return False
        if not self.paused:
            logger.warning("Scraper is not paused")
            return False

        try:
            self.paused = False
            if self.yahoo_finance_scraper:
                self.yahoo_finance_scraper.paused = False
            logger.info("Scraper resumed successfully")
            return True
        except Exception as e:
            logger.error(f"Error resuming scraper: {e}")
            return False

    def get_status(self):
        """Get the current status of the scraper."""
        return {
            'running': self.running,
            'paused': self.paused,
            'active_scrapers': ['yahoo_finance'] if self.running else []
        } 