import threading
import time
import traceback
from app.database import Database
from app.utils.logging import setup_logger
import logging

logger = setup_logger()

class ScraperManager:
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.active = False
        self.scrapers = {
            'yahoo_finance': YahooFinanceScraper(db)
        }
        self.scraping_interval = 300  # 5 minutes
        self.scraping_thread = None
        self.stop_event = threading.Event()
        self._running = False
        self._thread = None
        self._ensure_scraper_states_table()
        self._ensure_scraper_metrics_table()

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

    def _ensure_scraper_metrics_table(self):
        """Ensure scraper_metrics table exists."""
        try:
            with self.db.connection_pool.get_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS scraper_metrics (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            scraper_name VARCHAR(100) NOT NULL,
                            timestamp DATETIME NOT NULL,
                            total_attempts INT DEFAULT 0,
                            successful INT DEFAULT 0,
                            failed INT DEFAULT 0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            INDEX idx_scraper_time (scraper_name, timestamp)
                        )
                    """)
                    connection.commit()
                    logger.info("Scraper metrics table verified/created")
        except Exception as e:
            logger.error(f"Error ensuring scraper metrics table: {str(e)}")
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
        """Update metrics for a specific scraper."""
        try:
            with self.db.connection_pool.get_connection() as connection:
                with connection.cursor() as cursor:
                    # Get or create current hour's metrics
                    cursor.execute("""
                        INSERT INTO scraper_metrics (scraper_name, timestamp, total_attempts, successful, failed)
                        VALUES (
                            %s, 
                            DATE_FORMAT(NOW(), '%Y-%m-%d %H:00:00'),
                            1,
                            CASE WHEN %s = 'SUCCESS' THEN 1 ELSE 0 END,
                            CASE WHEN %s = 'FAILED' THEN 1 ELSE 0 END
                        )
                        ON DUPLICATE KEY UPDATE
                            total_attempts = total_attempts + 1,
                            successful = successful + CASE WHEN %s = 'SUCCESS' THEN 1 ELSE 0 END,
                            failed = failed + CASE WHEN %s = 'FAILED' THEN 1 ELSE 0 END
                    """, (scraper_name, status, status, status, status))
                    connection.commit()
                    logger.debug(f"Updated metrics for {scraper_name}: {status}")
        except Exception as e:
            logger.error(f"Error updating scraper metrics: {str(e)}")
            # Try alternative timestamp format if the first one fails
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO scraper_metrics (scraper_name, timestamp, total_attempts, successful, failed)
                        VALUES (
                            %s, 
                            NOW(),
                            1,
                            CASE WHEN %s = 'SUCCESS' THEN 1 ELSE 0 END,
                            CASE WHEN %s = 'FAILED' THEN 1 ELSE 0 END
                        )
                        ON DUPLICATE KEY UPDATE
                            total_attempts = total_attempts + 1,
                            successful = successful + CASE WHEN %s = 'SUCCESS' THEN 1 ELSE 0 END,
                            failed = failed + CASE WHEN %s = 'FAILED' THEN 1 ELSE 0 END
                    """, (scraper_name, status, status, status, status))
                    connection.commit()
                    logger.debug(f"Updated metrics for {scraper_name} using alternative timestamp: {status}")
            except Exception as e2:
                logger.error(f"Error updating scraper metrics with alternative timestamp: {str(e2)}")

    def get_scraper_metrics(self, hours=1):
        """Get aggregated metrics for all scrapers for the last X hours."""
        try:
            with self.db.connection_pool.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = """
                    SELECT 
                        scraper_name,
                        SUM(total_attempts) as total_attempts,
                        SUM(successful) as successful,
                        SUM(failed) as failed
                    FROM scraper_metrics
                    WHERE timestamp >= NOW() - INTERVAL %s HOUR
                    GROUP BY scraper_name
                    """
                    cursor.execute(query, (hours,))
                    results = cursor.fetchall()
                    
                    # Aggregate metrics across all scrapers
                    total_attempts = 0
                    total_successful = 0
                    total_failed = 0
                    scraper_stats = {}
                    
                    for result in results:
                        scraper_name = result['scraper_name']
                        attempts = result['total_attempts'] or 0
                        successful = result['successful'] or 0
                        failed = result['failed'] or 0
                        
                        total_attempts += attempts
                        total_successful += successful
                        total_failed += failed
                        
                        scraper_stats[scraper_name] = {
                            'total_attempts': attempts,
                            'successful': successful,
                            'failed': failed,
                            'success_rate': round((successful / attempts * 100) if attempts > 0 else 0, 2)
                        }
                    
                    return {
                        'total': {
                            'total_attempts': total_attempts,
                            'successful': total_successful,
                            'failed': total_failed,
                            'success_rate': round((total_successful / total_attempts * 100) if total_attempts > 0 else 0, 2)
                        },
                        'by_scraper': scraper_stats
                    }
        except Exception as e:
            logger.error(f"Error getting scraper metrics: {str(e)}")
            return {
                'total': {
                    'total_attempts': 0,
                    'successful': 0,
                    'failed': 0,
                    'success_rate': 0
                },
                'by_scraper': {}
            }

    def scrape_articles(self):
        """Run all scrapers and record metrics."""
        while not self.stop_event.is_set():
            for scraper_name, scraper in self.scrapers.items():
                if not self.active:
                    break

                total_attempts = 0
                successful = 0
                failed = 0

                try:
                    # Get articles to scrape
                    articles = scraper.get_articles_to_scrape()
                    total_attempts = len(articles)

                    for article in articles:
                        try:
                            # Scrape and save article
                            article_data = scraper.scrape_article(article['url'])
                            if article_data:
                                self.db.add_article(article_data)
                                successful += 1
                                self.db.add_scraping_log(
                                    status='SUCCESS',
                                    source_type=scraper_name,
                                    url=article['url']
                                )
                            else:
                                failed += 1
                                self.db.add_scraping_log(
                                    status='FAILED',
                                    source_type=scraper_name,
                                    url=article['url'],
                                    error_message='No article data returned'
                                )
                        except Exception as e:
                            failed += 1
                            self.db.add_scraping_log(
                                status='ERROR',
                                source_type=scraper_name,
                                url=article['url'],
                                error_message=str(e)
                            )
                            self.logger.error(f"Error scraping article {article['url']}: {str(e)}")

                    # Record metrics for this scraper run
                    self.db.add_scraper_metrics(
                        scraper_name=scraper_name,
                        total_attempts=total_attempts,
                        successful=successful,
                        failed=failed
                    )

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