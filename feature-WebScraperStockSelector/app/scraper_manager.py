import threading
import time
import traceback
from app.database import Database
from app.utils.logging import setup_logger
from app.scrapers.yahoo_finance import YahooFinanceScraper
import logging

logger = setup_logger()

class ScraperManager:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.active = False
        self.scrapers = {}  # Initialize empty dict, will add scrapers later
        self.scraping_interval = 300  # 5 minutes
        self.scraping_thread = None
        self.stop_event = threading.Event()
        self._running = False
        self._thread = None
        
        # In-memory metrics storage
        self.metrics = {
            'total': {
                'total_attempts': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0
            },
            'by_scraper': {}
        }
        
        self._ensure_scraper_states_table()
        
        # Initialize default scrapers
        self.init_default_scrapers()

    def init_default_scrapers(self):
        """Initialize default scrapers."""
        try:
            # Add Yahoo Finance scraper
            yahoo_scraper = YahooFinanceScraper(self.db)
            self.add_scraper('yahoo_finance', yahoo_scraper)
            logger.info("Default scrapers initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing default scrapers: {str(e)}")
            raise

    def _ensure_scraper_states_table(self):
        """Ensure scraper_states table exists."""
        try:
            with self.db.connection_pool.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS scraper_states (
                            scraper_name VARCHAR(100) PRIMARY KEY,
                            is_paused BOOLEAN NOT NULL DEFAULT FALSE,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                        )
                    """)
                    connection.commit()
                    logger.info("Scraper states table verified/created")
        except Exception as e:
            logger.error(f"Error ensuring scraper states table: {str(e)}")
            raise

    def _get_pause_state(self, scraper_name):
        """Get pause state from database."""
        try:
            with self.db.connection_pool.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute(
                        "SELECT is_paused FROM scraper_states WHERE scraper_name = %s",
                        (scraper_name,)
                    )
                    result = cursor.fetchone()
                    is_paused = bool(result['is_paused']) if result else False
                    logger.debug(f"Retrieved pause state for {scraper_name}: {is_paused}")
                    return is_paused
        except Exception as e:
            logger.error(f"Error getting pause state for {scraper_name}: {str(e)}")
            return False

    def _save_pause_state(self, scraper_name, is_paused):
        """Save pause state to database."""
        try:
            with self.db.connection_pool.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO scraper_states (scraper_name, is_paused)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE
                            is_paused = VALUES(is_paused),
                            updated_at = CURRENT_TIMESTAMP
                    """, (scraper_name, is_paused))
                    connection.commit()
                    logger.info(f"Saved pause state for {scraper_name}: {is_paused}")
        except Exception as e:
            logger.error(f"Error saving pause state for {scraper_name}: {str(e)}")
            raise

    def add_scraper(self, name, scraper):
        """Add a scraper to the manager."""
        self.scrapers[name] = scraper
        # Set manager reference in scraper
        if hasattr(scraper, 'set_manager'):
            scraper.set_manager(self)
        self._save_pause_state(name, False)
        logger.info(f"Added scraper: {name}")

    def remove_scraper(self, name):
        """Remove a scraper from the manager."""
        if name in self.scrapers:
            del self.scrapers[name]
            try:
                with self.db.connection_pool.get_connection() as connection:
                    with connection.cursor() as cursor:
                        cursor.execute("DELETE FROM scraper_states WHERE scraper_name = %s", (name,))
                        connection.commit()
                logger.info(f"Removed scraper: {name}")
            except Exception as e:
                logger.error(f"Error removing scraper state: {str(e)}")

    def is_paused(self, scraper_name):
        """Check if a specific scraper is paused."""
        return self._get_pause_state(scraper_name)

    def pause_scraper(self, scraper_name):
        """Pause a specific scraper."""
        if scraper_name in self.scrapers:
            try:
                self._save_pause_state(scraper_name, True)
                logger.info(f"Successfully paused scraper: {scraper_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to pause scraper {scraper_name}: {str(e)}")
                return False
        logger.warning(f"Attempted to pause unknown scraper: {scraper_name}")
        return False

    def resume_scraper(self, scraper_name):
        """Resume a specific scraper."""
        if scraper_name in self.scrapers:
            try:
                self._save_pause_state(scraper_name, False)
                logger.info(f"Successfully resumed scraper: {scraper_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to resume scraper {scraper_name}: {str(e)}")
                return False
        logger.warning(f"Attempted to resume unknown scraper: {scraper_name}")
        return False

    def get_scraper_status(self, scraper_name):
        """Get the status of a specific scraper."""
        if scraper_name not in self.scrapers:
            return "Not Found"
        is_paused = self._get_pause_state(scraper_name)
        status = "Paused" if is_paused else "Running"
        logger.debug(f"Status for {scraper_name}: {status}")
        return status

    def update_scraper_metrics(self, scraper_name, status):
        """Update metrics for a specific scraper in memory."""
        # Initialize scraper metrics if not exists
        if scraper_name not in self.metrics['by_scraper']:
            self.metrics['by_scraper'][scraper_name] = {
                'total_attempts': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0
            }
        
        # Update scraper-specific metrics
        self.metrics['by_scraper'][scraper_name]['total_attempts'] += 1
        if status == 'SUCCESS':
            self.metrics['by_scraper'][scraper_name]['successful'] += 1
        elif status in ['FAILED', 'ERROR']:
            self.metrics['by_scraper'][scraper_name]['failed'] += 1
            
        # Update success rate
        attempts = self.metrics['by_scraper'][scraper_name]['total_attempts']
        successful = self.metrics['by_scraper'][scraper_name]['successful']
        self.metrics['by_scraper'][scraper_name]['success_rate'] = round((successful / attempts * 100) if attempts > 0 else 0, 2)
        
        # Update total metrics
        self.metrics['total']['total_attempts'] += 1
        if status == 'SUCCESS':
            self.metrics['total']['successful'] += 1
        elif status in ['FAILED', 'ERROR']:
            self.metrics['total']['failed'] += 1
            
        # Update total success rate
        total_attempts = self.metrics['total']['total_attempts']
        total_successful = self.metrics['total']['successful']
        self.metrics['total']['success_rate'] = round((total_successful / total_attempts * 100) if total_attempts > 0 else 0, 2)

    def get_scraper_metrics(self, hours=1):
        """Get current scraper metrics from memory."""
        return self.metrics

    def scrape_articles(self):
        """Run all scrapers and record metrics."""
        while not self.stop_event.is_set():
            for scraper_name, scraper in self.scrapers.items():
                if not self.active:
                    break

                try:
                    # Get articles to scrape
                    articles = scraper.get_articles_to_scrape()
                    
                    for article in articles:
                        try:
                            # Scrape and save article
                            article_data = scraper.scrape_article(article['url'])
                            if article_data:
                                self.db.add_article(article_data)
                                self.update_scraper_metrics(scraper_name, 'SUCCESS')
                                self.db.add_scraping_log(
                                    status='SUCCESS',
                                    source_type=scraper_name,
                                    url=article['url']
                                )
                            else:
                                self.update_scraper_metrics(scraper_name, 'FAILED')
                                self.db.add_scraping_log(
                                    status='FAILED',
                                    source_type=scraper_name,
                                    url=article['url'],
                                    error_message='No article data returned'
                                )
                        except Exception as e:
                            self.update_scraper_metrics(scraper_name, 'ERROR')
                            self.db.add_scraping_log(
                                status='ERROR',
                                source_type=scraper_name,
                                url=article['url'],
                                error_message=str(e)
                            )
                            self.logger.error(f"Error scraping article {article['url']}: {str(e)}")

                except Exception as e:
                    self.logger.error(f"Error in scraper {scraper_name}: {str(e)}")
                    self.db.add_scraping_log(
                        status='ERROR',
                        source_type=scraper_name,
                        error_message=f"Scraper error: {str(e)}"
                    )

            # Wait for the next interval
            self.stop_event.wait(self.scraping_interval)

    def start(self):
        """Start the scraping process."""
        if not self.active:
            self.active = True
            self.stop_event.clear()
            self.scraping_thread = threading.Thread(target=self.scrape_articles)
            self.scraping_thread.start()
            self.logger.info("Scraper manager started")
            return True
        return False

    def stop(self):
        """Stop the scraping process."""
        if self.active:
            self.active = False
            self.stop_event.set()
            if self.scraping_thread:
                self.scraping_thread.join()
            self.logger.info("Scraper manager stopped")
            return True
        return False

    def get_status(self):
        """Get the current status of the scraper manager."""
        return {
            'active': self.active,
            'metrics': self.db.get_scraper_metrics(),
            'recent_logs': self.db.get_scraping_logs(limit=10)
        }

    def _run_loop(self):
        """Main loop for running scrapers."""
        while self._running:
            try:
                for name, scraper in self.scrapers.items():
                    # Always check pause state from database
                    if not self._get_pause_state(name):
                        logger.debug(f"Running scraper: {name}")
                        try:
                            scraper.scrape_feed()
                        except Exception as e:
                            logger.error(f"Error running scraper {name}: {str(e)}")
                            logger.error(traceback.format_exc())
                            # Update metrics for failed run
                            self.update_scraper_metrics(name, 'FAILED')
                    else:
                        logger.debug(f"Skipping paused scraper: {name}")
                
                time.sleep(60)  # Wait 60 seconds between cycles
            except Exception as e:
                logger.error(f"Error in scraper manager loop: {str(e)}")
                logger.error(traceback.format_exc())
                time.sleep(10)  # Wait 10 seconds on error before retrying

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

    def get_all_statuses(self):
        """Get the status of all scrapers."""
        return {name: self.get_scraper_status(name) for name in self.scrapers}

    def init_app(self, app):
        """Initialize the scraper manager with Flask app context."""
        try:
            # Store app reference
            self.app = app
            
            # Ensure required tables exist
            self._ensure_scraper_states_table()
            
            # Initialize default scrapers
            self.init_default_scrapers()
            
            logger.info("Scraper manager initialized with app context")
            return True
        except Exception as e:
            logger.error(f"Error initializing scraper manager with app: {str(e)}")
            return False 