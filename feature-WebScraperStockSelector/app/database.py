import mysql.connector
from mysql.connector import Error, pooling
import os
from datetime import datetime, timezone
import json
from app.utils.logging import setup_logger
from dotenv import load_dotenv
import pytz

load_dotenv()

logger = setup_logger()

class Database:
    def __init__(self):
        """Initialize database connection pool"""
        self.pool_config = {
            'pool_name': 'mypool',
            'pool_size': 5,
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DB', 'stock_scraper'),
            'port': int(os.getenv('MYSQL_PORT', 3306)),
            'pool_reset_session': True
        }
        try:
            self.connection_pool = mysql.connector.pooling.MySQLConnectionPool(**self.pool_config)
            logger.info("Database connection pool created successfully")
            self.create_tables()  # Create tables on initialization
        except Error as e:
            logger.error(f"Error creating connection pool: {e}")
            raise

    def get_connection(self):
        """Get a connection from the pool"""
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

    def add_article(self, article_data):
        """Add a new article to the database"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO articles (title, link, content, source, published_date, scraped_date, symbols)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    content = VALUES(content),
                    source = VALUES(source),
                    published_date = VALUES(published_date),
                    scraped_date = VALUES(scraped_date),
                    symbols = VALUES(symbols)
            """

            symbols_json = json.dumps(article_data.get('symbols', []))
            values = (
                article_data.get('title', ''),
                article_data.get('link', ''),
                article_data.get('content', ''),
                article_data.get('source', ''),
                article_data.get('published_date'),
                article_data.get('scraped_date', datetime.now()),
                symbols_json
            )

            cursor.execute(query, values)
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Error adding article: {e}")
            return False
        finally:
            if connection:
                connection.close()

    def get_recent_articles(self, limit=10, offset=0):
        """Get recent articles with pagination."""
        try:
            with self.connection_pool.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    query = """
                    SELECT id, title, link, content, source, published_date, scraped_date, symbols
                    FROM articles
                    WHERE NOT is_deleted
                    ORDER BY published_date DESC
                    LIMIT %s OFFSET %s
                    """
                    cursor.execute(query, (limit, offset))
                    articles = cursor.fetchall()
                    
                    # Convert datetime objects to ISO format strings
                    for article in articles:
                        if article.get('published_date'):
                            article['published_date'] = article['published_date'].isoformat()
                        if article.get('scraped_date'):
                            article['scraped_date'] = article['scraped_date'].isoformat()
                        # Parse JSON symbols
                        if article.get('symbols'):
                            article['symbols'] = json.loads(article['symbols'])
                        else:
                            article['symbols'] = []
                        # Add URL field for frontend compatibility
                        article['url'] = article['link']
                    
                    return articles
        except Exception as e:
            logger.error(f"Error getting recent articles: {str(e)}")
            return []

    def add_scraping_log(self, log_data):
        """Add a new scraping log entry"""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO scraping_logs (timestamp, status, source_type, url, error_message)
                VALUES (%s, %s, %s, %s, %s)
            """
            values = (
                log_data.get('timestamp', datetime.now()),
                log_data.get('status', 'UNKNOWN'),
                log_data.get('source_type', ''),
                log_data.get('url', ''),
                log_data.get('error_message', '')
            )

            cursor.execute(query, values)
            connection.commit()
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Error adding scraping log: {e}")
            return False
        finally:
            if connection:
                connection.close()

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
                        SUM(CASE WHEN status = 'ERROR' THEN 1 ELSE 0 END) as failed
                    FROM scraping_logs
                    WHERE timestamp >= NOW() - INTERVAL %s HOUR
                    """
                    cursor.execute(query, (hours,))
                    stats = cursor.fetchone()
                    
                    if stats:
                        total = stats['total_attempts'] or 0
                        successful = stats['successful'] or 0
                        failed = stats['failed'] or 0
                        
                        return {
                            'total_attempts': total,
                            'successful': successful,
                            'failed': failed,
                            'success_rate': round((successful / total * 100) if total > 0 else 0, 2)
                        }
                    return {
                        'total_attempts': 0,
                        'successful': 0,
                        'failed': 0,
                        'success_rate': 0
                    }
        except Exception as e:
            logger.error(f"Error getting scraping stats: {str(e)}")
            return {
                'total_attempts': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0
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

    def get_total_articles(self):
        """Get the total number of articles in the database."""
        connection = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles WHERE NOT is_deleted")
            count = cursor.fetchone()[0]
            return count
        except Error as e:
            logger.error(f"Error getting total articles count: {e}")
            return 0
        finally:
            if connection:
                connection.close()

    def get_article_count(self):
        """Get the total number of articles in the database."""
        try:
            with self.connection_pool.get_connection() as connection:
                with connection.cursor(dictionary=True) as cursor:
                    cursor.execute("SELECT COUNT(*) as count FROM articles WHERE NOT is_deleted")
                    result = cursor.fetchone()
                    return result['count'] if result else 0
        except Exception as e:
            logger.error(f"Error getting article count: {str(e)}")
            return 0

# Create a global instance
db = Database() 