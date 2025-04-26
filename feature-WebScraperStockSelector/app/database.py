import mysql.connector
from mysql.connector import Error, pooling
import os
from datetime import datetime, timezone
import json
from app.utils.logging import setup_logger
from dotenv import load_dotenv
import pytz
import time
from functools import wraps

load_dotenv()

logger = setup_logger()

def retry_on_error(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Error as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries ({max_retries}) reached for {func.__name__}: {e}")
                        raise
                    logger.warning(f"Retry {retries}/{max_retries} for {func.__name__} due to: {e}")
                    time.sleep(delay * retries)  # Exponential backoff
            return None
        return wrapper
    return decorator

class Database:
    def __init__(self):
        """Initialize database connection pool"""
        from config import Config
        self.pool_config = {
            'pool_name': 'mypool',
            'pool_size': Config.DB_POOL_SIZE,
            'pool_reset_session': True,
            'host': Config.MYSQL_HOST,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'database': Config.MYSQL_DB,
            'port': Config.MYSQL_PORT,
        }
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(**self.pool_config)
            logger.info("Database connection pool created successfully")
            self.create_tables()  # Create tables on initialization
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            raise

    @retry_on_error()
    def get_connection(self):
        """Get a connection from the pool with retry logic"""
        try:
            connection = self.connection_pool.get_connection()
            return connection
        except Error as e:
            logger.error(f"Error getting connection from pool: {e}")
            raise

    def execute_query(self, query, params=None):
        """Execute a query with automatic connection management"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                connection.commit()
                return cursor.lastrowid
            else:
                return cursor.fetchall()
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Error executing query: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def check_connection(self):
        """Check if we can get a working connection from the pool"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return result is not None and result[0] == 1
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
        finally:
            if connection:
                try:
                    connection.close()
                except Exception:
                    pass

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            # Articles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(500) NOT NULL,
                    link VARCHAR(500) UNIQUE NOT NULL,
                    content TEXT,
                    source VARCHAR(100),
                    published_date DATETIME,
                    scraped_date DATETIME,
                    symbols JSON,
                    is_deleted BOOLEAN DEFAULT FALSE,
                    is_analyzed BOOLEAN DEFAULT FALSE,
                    analyzed_at DATETIME DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_scraped_date (scraped_date),
                    INDEX idx_published_date (published_date),
                    INDEX idx_is_deleted (is_deleted),
                    INDEX idx_is_analyzed (is_analyzed)
                )
            """)

            # Scraping logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    timestamp DATETIME NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    source_type VARCHAR(100),
                    url VARCHAR(500),
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_timestamp (timestamp),
                    INDEX idx_status (status)
                )
            """)

            # Ticker symbols table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ticker_symbols (
                    symbol VARCHAR(10) PRIMARY KEY,
                    exchange VARCHAR(50),
                    company_name VARCHAR(255),
                    is_active BOOLEAN DEFAULT TRUE,
                    last_verified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_ticker_symbols_active (is_active)
                )
            """)

            # Analyzer state table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analyzer_state (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    is_paused BOOLEAN DEFAULT FALSE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            connection.commit()
            cursor.close()
            logger.info("Database tables created successfully")
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def verify_tables(self):
        """Verify that all required tables exist and have the correct structure."""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            
            # Check if tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """)
            existing_tables = {row[0] for row in cursor.fetchall()}
            logger.info(f"Existing tables in database: {existing_tables}")
            
            # Create tables if they don't exist
            if 'articles' not in existing_tables or 'scraping_logs' not in existing_tables:
                logger.info("Creating missing tables...")
                self.create_tables()
            
            # Verify articles table structure
            cursor.execute("DESCRIBE articles")
            columns = {row[0] for row in cursor.fetchall()}
            logger.info(f"Articles table columns: {columns}")
            
            # Verify scraping_logs table structure
            cursor.execute("DESCRIBE scraping_logs")
            log_columns = {row[0] for row in cursor.fetchall()}
            logger.info(f"Scraping logs table columns: {log_columns}")
            
            cursor.close()
        except Error as e:
            logger.error(f"Error verifying tables: {e}")
            raise
        finally:
            if connection:
                connection.close()

    @retry_on_error()
    def add_article(self, article_data):
        """Add a new article to the database with retry logic"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO articles (
                    title, link, content, source, published_date, 
                    scraped_date, symbols, is_analyzed, analyzed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    content = VALUES(content),
                    source = VALUES(source),
                    published_date = VALUES(published_date),
                    scraped_date = VALUES(scraped_date),
                    symbols = VALUES(symbols)
            """
            
            params = (
                article_data.get('title'),
                article_data.get('link'),
                article_data.get('content'),
                article_data.get('source'),
                article_data.get('published_date'),
                datetime.now(timezone.utc),
                json.dumps(article_data.get('symbols', [])),
                False,  # is_analyzed
                None   # analyzed_at
            )
            
            cursor.execute(query, params)
            connection.commit()
            article_id = cursor.lastrowid
            
            # Log successful article addition
            logger.info(f"Successfully added/updated article: {article_data.get('title')} (ID: {article_id})")
            
            return article_id
            
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"Error adding article: {e}")
            raise
        finally:
            if connection:
                connection.close()

    def get_recent_articles(self, limit=10, offset=0, sort_by='published_date', sort_order='DESC'):
        """Get recent articles with pagination and sorting."""
        try:
            valid_sort_fields = ['published_date', 'scraped_date']
            valid_sort_orders = ['ASC', 'DESC']
            
            # Validate sort parameters
            if sort_by not in valid_sort_fields:
                sort_by = 'published_date'
            if sort_order.upper() not in valid_sort_orders:
                sort_order = 'DESC'
            
            query = """
                SELECT id, title, link, content, source, published_date, scraped_date,
                       symbols, validated_symbols
                FROM articles
                WHERE NOT is_deleted
                ORDER BY {} {}
                LIMIT %s OFFSET %s
            """.format(sort_by, sort_order)
            
            articles = self.execute_query(query, (limit, offset))
            
            if not articles:
                return []
            
            # Process articles
            for article in articles:
                # Handle datetime fields
                if article.get('published_date'):
                    article['published_date'] = article['published_date'].isoformat()
                if article.get('scraped_date'):
                    article['scraped_date'] = article['scraped_date'].isoformat()
                
                # Parse JSON fields safely
                try:
                    article['symbols'] = json.loads(article.get('symbols') or '[]')
                except (TypeError, json.JSONDecodeError):
                    article['symbols'] = []
                    
                try:
                    article['validated_symbols'] = json.loads(article.get('validated_symbols') or '[]')
                except (TypeError, json.JSONDecodeError):
                    article['validated_symbols'] = []
                
                # Add content preview
                content = article.get('content', '')
                if content:
                    # Create a preview of first 200 characters
                    article['content_preview'] = content[:200] + '...' if len(content) > 200 else content
                else:
                    article['content_preview'] = 'No content available'
                
                # Add URL field for frontend compatibility
                article['url'] = article['link']
            
            return articles
            
        except Exception as e:
            logger.error(f"Error getting recent articles: {str(e)}")
            return []

    def add_scraping_log(self, status, source_type=None, url=None, error_message=None):
        """Add a scraping log entry."""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO scraping_logs (timestamp, status, source_type, url, error_message)
                VALUES (NOW(), %s, %s, %s, %s)
                """,
                (status, source_type, url, error_message)
            )
            connection.commit()
            cursor.close()
            connection.close()
            logger.info(f"Added scraping log: {status} for {source_type}")
        except Exception as e:
            logger.error(f"Error adding scraping log: {str(e)}")
            raise

    def get_scraping_logs(self, limit=50):
        """Get recent scraping logs."""
        try:
            with self.connection_pool.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = """
                    SELECT timestamp, status, source_type, url, error_message
                    FROM scraping_logs
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """
                    cursor.execute(query, (limit,))
                    logs = cursor.fetchall()
                    
                    # Convert datetime objects to ISO format strings
                    for log in logs:
                        if log.get('timestamp'):
                            log['timestamp'] = log['timestamp'].isoformat()
                    
                    return logs
        except Exception as e:
            logger.error(f"Error getting scraping logs: {str(e)}")
            return []

    def get_scraping_stats(self, hours=1):
        """Get scraping statistics for the last X hours."""
        try:
            with self.connection_pool.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = """
                    SELECT 
                        COUNT(*) as total_attempts,
                        SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                        SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as failed,
                        SUM(CASE WHEN status = 'DUPLICATE' THEN 1 ELSE 0 END) as duplicates
                    FROM scraping_logs
                    WHERE timestamp >= NOW() - INTERVAL %s HOUR
                    """
                    cursor.execute(query, (hours,))
                    stats = cursor.fetchone()
                    
                    if stats:
                        total = stats['total_attempts'] or 0
                        successful = stats['successful'] or 0
                        failed = stats['failed'] or 0
                        duplicates = stats['duplicates'] or 0
                        
                        return {
                            'total_attempts': total,
                            'successful': successful,
                            'failed': failed,
                            'duplicates': duplicates,
                            'success_rate': round((successful / total * 100) if total > 0 else 0, 2),
                            'failure_rate': round((failed / total * 100) if total > 0 else 0, 2)
                        }
                    return {
                        'total_attempts': 0,
                        'successful': 0,
                        'failed': 0,
                        'duplicates': 0,
                        'success_rate': 0,
                        'failure_rate': 0
                    }
        except Exception as e:
            logger.error(f"Error getting scraping stats: {str(e)}")
            return {
                'total_attempts': 0,
                'successful': 0,
                'failed': 0,
                'duplicates': 0,
                'success_rate': 0,
                'failure_rate': 0
            }

    def mark_article_deleted(self, article_url):
        """Mark an article as deleted"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            query = "UPDATE articles SET is_deleted = TRUE WHERE link = %s"
            cursor.execute(query, (article_url,))
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Error marking article as deleted: {e}")
            return False
        finally:
            if connection:
                connection.close()

    def get_article_by_url(self, article_url):
        """Get article details by URL"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)

            query = "SELECT * FROM articles WHERE link = %s AND NOT is_deleted"
            cursor.execute(query, (article_url,))
            article = cursor.fetchone()

            if article:
                article['symbols'] = json.loads(article['symbols']) if article['symbols'] else []

            return article
        except Error as e:
            logger.error(f"Error getting article by URL: {e}")
            return None
        finally:
            if connection:
                connection.close()

    def close(self):
        """Close database connection"""
        try:
            if self.connection_pool and self.connection_pool.get_connection().is_connected():
                self.connection_pool.get_connection().close()
                logger.info("Database connection closed")
        except Error as e:
            logger.error(f"Error closing database connection: {e}")

    def get_article_count(self):
        """
        Get the total count of non-deleted articles in the database.
        Uses an optimized query with an index on the deleted column for better performance.
        
        Returns:
            int: The total number of non-deleted articles
        """
        try:
            with self.connection_pool.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT COUNT(*) as count FROM articles WHERE is_deleted = 0")
                    result = cursor.fetchone()
                    return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error getting article count: {str(e)}")
            return 0

    def add_scraper_metrics(self, scraper_name, total_attempts, successful, failed):
        """Add a scraper metrics entry."""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO scraper_metrics (scraper_name, timestamp, total_attempts, successful, failed)
                VALUES (%s, NOW(), %s, %s, %s)
                """,
                (scraper_name, total_attempts, successful, failed)
            )
            connection.commit()
            cursor.close()
            connection.close()
            logger.info(f"Added metrics for {scraper_name}: {successful}/{total_attempts} successful")
        except Exception as e:
            logger.error(f"Error adding scraper metrics: {str(e)}")
            raise

    def get_scraper_metrics(self, hours=24):
        """Get aggregated scraper metrics for the specified time period."""
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT 
                    scraper_name,
                    SUM(total_attempts) as total_attempts,
                    SUM(successful) as successful,
                    SUM(failed) as failed,
                    MAX(timestamp) as last_run
                FROM scraper_metrics
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
                GROUP BY scraper_name
                """,
                (hours,)
            )
            metrics = cursor.fetchall()
            cursor.close()
            connection.close()

            # Format the metrics
            formatted_metrics = []
            for metric in metrics:
                formatted_metrics.append({
                    'scraper_name': metric['scraper_name'],
                    'total_attempts': metric['total_attempts'],
                    'successful': metric['successful'],
                    'failed': metric['failed'],
                    'success_rate': round((metric['successful'] / metric['total_attempts'] * 100), 2) if metric['total_attempts'] > 0 else 0,
                    'last_run': metric['last_run'].strftime('%Y-%m-%d %H:%M:%S') if metric['last_run'] else None
                })
            return formatted_metrics
        except Exception as e:
            logger.error(f"Error getting scraper metrics: {str(e)}")
            raise

# Create a global instance
db = Database() 