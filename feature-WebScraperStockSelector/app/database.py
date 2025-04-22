import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import json
from app.utils.logging import setup_logger

logger = setup_logger()

class Database:
    def __init__(self):
        self.connection = None
        self.connect()
        self.verify_tables()

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=os.getenv('MYSQL_HOST', '127.0.0.1'),
                user=os.getenv('MYSQL_USER', 'botstonkwar_user'),
                password=os.getenv('MYSQL_PASSWORD', 'botstonkwar_password'),
                database=os.getenv('MYSQL_DB', 'botstonkwar-db'),
                port=int(os.getenv('MYSQL_PORT', '3306'))
            )
            logger.info("Successfully connected to MySQL database")
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            raise

    def ensure_connection(self):
        """Ensure database connection is active"""
        try:
            if self.connection and self.connection.is_connected():
                return
            self.connect()
        except Error as e:
            logger.error(f"Error reconnecting to database: {e}")
            raise

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()

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

            self.connection.commit()
            cursor.close()
            logger.info("Database tables created successfully")
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def verify_tables(self):
        """Verify that all required tables exist and have the correct structure."""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()
            
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

    def add_article(self, article_data):
        """Add a new article to the database"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()

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
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Error adding article: {e}")
            return False

    def get_recent_articles(self, limit=10, offset=0):
        """Get recent articles from database"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)

            query = """
                SELECT * FROM articles 
                WHERE NOT is_deleted 
                ORDER BY scraped_date DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(query, (limit, offset))
            articles = cursor.fetchall()

            # Get total count
            cursor.execute("SELECT COUNT(*) as count FROM articles WHERE NOT is_deleted")
            total_count = cursor.fetchone()['count']

            cursor.close()

            # Format articles for display
            for article in articles:
                article['symbols'] = json.loads(article['symbols']) if article['symbols'] else []
                article['symbols'] = ', '.join(article['symbols'])
                if article['content']:
                    article['content_preview'] = article['content'][:200] + '...' if len(article['content']) > 200 else article['content']
                else:
                    article['content_preview'] = ''

            return articles, total_count
        except Error as e:
            logger.error(f"Error getting recent articles: {e}")
            return [], 0

    def add_scraping_log(self, log_data):
        """Add a new scraping log entry"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()

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
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Error adding scraping log: {e}")
            return False

    def get_scraping_logs(self, limit=20):
        """Get recent scraping logs"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)

            query = """
                SELECT * FROM scraping_logs 
                ORDER BY timestamp DESC 
                LIMIT %s
            """
            cursor.execute(query, (limit,))
            logs = cursor.fetchall()
            cursor.close()
            return logs
        except Error as e:
            logger.error(f"Error getting scraping logs: {e}")
            return []

    def get_scraping_stats(self, hours=1):
        """Get scraping statistics for the last N hours"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)
            
            query = """
                SELECT 
                    COUNT(*) as total_attempts,
                    SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed
                FROM scraping_logs 
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
            """
            cursor.execute(query, (hours,))
            stats = cursor.fetchone()
            cursor.close()
            
            total = stats['total_attempts'] or 0
            successful = stats['successful'] or 0
            failed = stats['failed'] or 0
            
            return {
                'total_attempts': total,
                'successful': successful,
                'failed': failed,
                'success_rate': (successful / total * 100) if total > 0 else 0
            }
        except Error as e:
            logger.error(f"Error getting scraping stats: {e}")
            return {
                'total_attempts': 0,
                'successful': 0,
                'failed': 0,
                'success_rate': 0
            }

    def mark_article_deleted(self, article_url):
        """Mark an article as deleted"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor()

            query = "UPDATE articles SET is_deleted = TRUE WHERE link = %s"
            cursor.execute(query, (article_url,))
            self.connection.commit()
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Error marking article as deleted: {e}")
            return False

    def get_article_by_url(self, article_url):
        """Get article details by URL"""
        try:
            self.ensure_connection()
            cursor = self.connection.cursor(dictionary=True)

            query = "SELECT * FROM articles WHERE link = %s AND NOT is_deleted"
            cursor.execute(query, (article_url,))
            article = cursor.fetchone()
            cursor.close()

            if article:
                article['symbols'] = json.loads(article['symbols']) if article['symbols'] else []

            return article
        except Error as e:
            logger.error(f"Error getting article by URL: {e}")
            return None

    def close(self):
        """Close database connection"""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                logger.info("Database connection closed")
        except Error as e:
            logger.error(f"Error closing database connection: {e}")

    def check_connection(self):
        """Check if the database connection is active."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False

    def get_total_articles(self):
        """Get the total number of articles in the database."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles WHERE NOT is_deleted")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            logger.error(f"Error getting total articles count: {e}")
            return 0 