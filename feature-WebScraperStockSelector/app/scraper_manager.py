import threading
import time
import traceback
from app.database import Database
from app.utils.logging import setup_logger

logger = setup_logger()

class ScraperManager:
    def __init__(self):
        self.scrapers = {}
        self._paused_scrapers = set()  # Track which scrapers are paused
        self.db = Database()
        self._running = False
        self._thread = None

    def add_scraper(self, name, scraper):
        """Add a scraper to the manager."""
        self.scrapers[name] = scraper
        logger.info(f"Added scraper: {name}")

    def remove_scraper(self, name):
        """Remove a scraper from the manager."""
        if name in self.scrapers:
            del self.scrapers[name]
            self._paused_scrapers.discard(name)
            logger.info(f"Removed scraper: {name}")

    def is_paused(self, scraper_name):
        """Check if a specific scraper is paused."""
        return scraper_name in self._paused_scrapers

    def pause_scraper(self, scraper_name):
        """Pause a specific scraper."""
        if scraper_name in self.scrapers:
            self._paused_scrapers.add(scraper_name)
            logger.info(f"Paused scraper: {scraper_name}")
            return True
        return False

    def resume_scraper(self, scraper_name):
        """Resume a specific scraper."""
        if scraper_name in self.scrapers:
            self._paused_scrapers.discard(scraper_name)
            logger.info(f"Resumed scraper: {scraper_name}")
            return True
        return False

    def pause_all(self):
        """Pause all scrapers."""
        for name in self.scrapers:
            self._paused_scrapers.add(name)
        logger.info("Paused all scrapers")

    def resume_all(self):
        """Resume all scrapers."""
        self._paused_scrapers.clear()
        logger.info("Resumed all scrapers")

    def get_scraper_status(self, scraper_name):
        """Get the status of a specific scraper."""
        if scraper_name not in self.scrapers:
            return "Not Found"
        return "Paused" if self.is_paused(scraper_name) else "Running"

    def get_all_statuses(self):
        """Get the status of all scrapers."""
        return {name: self.get_scraper_status(name) for name in self.scrapers}

    def run(self):
        """Run the scraper manager."""
        if self._running:
            logger.warning("Scraper manager is already running")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop)
        self._thread.daemon = True
        self._thread.start()
        logger.info("Scraper manager started")

    def stop(self):
        """Stop the scraper manager."""
        if not self._running:
            logger.warning("Scraper manager is not running")
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Scraper manager stopped")

    def _run_loop(self):
        """Main loop for running scrapers."""
        while self._running:
            try:
                for name, scraper in self.scrapers.items():
                    if not self.is_paused(name):
                        try:
                            scraper.scrape_feed()
                        except Exception as e:
                            logger.error(f"Error running scraper {name}: {str(e)}")
                            logger.error(traceback.format_exc())
                
                time.sleep(60)  # Wait 60 seconds between cycles
            except Exception as e:
                logger.error(f"Error in scraper manager loop: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(10)  # Wait 10 seconds on error before retrying 