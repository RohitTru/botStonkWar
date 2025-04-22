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
        self._load_pause_states()  # Load pause states from database

    def _load_pause_states(self):
        """Load pause states from database."""
        try:
            with self.db.connection_pool.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    # Create table if it doesn't exist
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS scraper_states (
                            scraper_name VARCHAR(100) PRIMARY KEY,
                            is_paused BOOLEAN NOT NULL DEFAULT FALSE,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        )
                    """)
                    connection.commit()

                    # Load states
                    cursor.execute("SELECT scraper_name, is_paused FROM scraper_states")
                    states = cursor.fetchall()
                    for state in states:
                        if state['is_paused']:
                            self._paused_scrapers.add(state['scraper_name'])
        except Exception as e:
            logger.error(f"Error loading pause states: {str(e)}")

    def _save_pause_state(self, scraper_name, is_paused):
        """Save pause state to database."""
        try:
            with self.db.connection_pool.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO scraper_states (scraper_name, is_paused)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE
                            is_paused = VALUES(is_paused)
                    """, (scraper_name, is_paused))
                    connection.commit()
        except Exception as e:
            logger.error(f"Error saving pause state: {str(e)}")

    def add_scraper(self, name, scraper):
        """Add a scraper to the manager."""
        self.scrapers[name] = scraper
        # Initialize pause state in database
        self._save_pause_state(name, False)
        logger.info(f"Added scraper: {name}")

    def remove_scraper(self, name):
        """Remove a scraper from the manager."""
        if name in self.scrapers:
            del self.scrapers[name]
            self._paused_scrapers.discard(name)
            # Remove from database
            try:
                with self.db.connection_pool.get_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM scraper_states WHERE scraper_name = %s", (name,))
                        connection.commit()
            except Exception as e:
                logger.error(f"Error removing scraper state: {str(e)}")
            logger.info(f"Removed scraper: {name}")

    def is_paused(self, scraper_name):
        """Check if a specific scraper is paused."""
        return scraper_name in self._paused_scrapers

    def pause_scraper(self, scraper_name):
        """Pause a specific scraper."""
        if scraper_name in self.scrapers:
            self._paused_scrapers.add(scraper_name)
            self._save_pause_state(scraper_name, True)
            logger.info(f"Paused scraper: {scraper_name}")
            return True
        return False

    def resume_scraper(self, scraper_name):
        """Resume a specific scraper."""
        if scraper_name in self.scrapers:
            self._paused_scrapers.discard(scraper_name)
            self._save_pause_state(scraper_name, False)
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