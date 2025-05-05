import mysql.connector
from mysql.connector import pooling
import logging
from datetime import datetime
from typing import List, Dict, Optional, Union
import json
import os

class Database:
    def __init__(self):
        """Initialize database connection pool"""
        try:
            # Try to get database name from environment, fallback to hardcoded value
            db_name = os.getenv('MYSQL_DATABASE')
            if not db_name or db_name == 'botstonkwar-db':
                db_name = 'botstonkwar_scraping_db'
                logging.warning(f"Using hardcoded database name: {db_name}")
            else:
                logging.info(f"Using database from environment: {db_name}")
            
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="sentiment_pool",
                pool_size=32,  # Increased from 10
                pool_reset_session=True,
                host=os.getenv('MYSQL_HOST', 'mysql'),
                port=3306,
                user=os.getenv('MYSQL_USER', 'root'),
                password=os.getenv('MYSQL_PASSWORD', ''),
                database=db_name,
                connect_timeout=60,
                autocommit=True
            )
            logging.info("Database connection pool initialized successfully")
            
            # Verify database connection and tables
            self._verify_database()
        except Exception as e:
            logging.error(f"Error initializing database pool: {str(e)}")
            raise

    def _verify_database(self):
        """Verify database connection and required tables"""
        try:
            # Check if we can connect to the database
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get current database name
                cursor.execute("SELECT DATABASE()")
                current_db = cursor.fetchone()[0]
                logging.info(f"Connected to database: {current_db}")
                
                # Check if articles table exists
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = 'articles'
                """)
                articles_exist = cursor.fetchone()[0]
                logging.info(f"Articles table exists: {articles_exist}")
                
                # Check if sentiment_analysis table exists
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.tables 
                    WHERE table_schema = DATABASE() 
                    AND table_name = 'sentiment_analysis'
                """)
                sentiment_exists = cursor.fetchone()[0]
                logging.info(f"Sentiment analysis table exists: {sentiment_exists}")
                
                if not articles_exist or not sentiment_exists:
                    error_msg = f"Required tables missing in database {current_db}. "
                    error_msg += "Please ensure you are connected to the correct database (botstonkwar_scraping_db)"
                    logging.error(error_msg)
                    raise Exception(error_msg)
                
        except Exception as e:
            logging.error(f"Database verification failed: {str(e)}")
            raise

    def get_connection(self):
        """Get a connection from the pool."""
        return self.pool.get_connection()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query and return results"""
        connection = None
        cursor = None
        try:
            connection = self.pool.get_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params)
            
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                connection.commit()
                return []
            
            result = cursor.fetchall()
            return result
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"Database error executing query: {str(e)}")
            logging.error(f"Query was: {query}")
            if params:
                logging.error(f"Parameters were: {params}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def execute_write(self, query: str, params: tuple = None) -> int:
        """Execute a write query and return the last insert ID."""
        connection = None
        cursor = None
        try:
            connection = self.pool.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.lastrowid
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"Database error executing write: {str(e)}")
            logging.error(f"Query was: {query}")
            if params:
                logging.error(f"Parameters were: {params}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def get_unanalyzed_articles(self, limit: int = 10) -> List[Dict]:
        """Get articles that haven't been analyzed yet, prioritizing:
        1. Recent articles (by published_date)
        2. Only articles with at least one validated symbol
        """
        query = """
        SELECT a.id, a.title, a.content, a.link, a.validated_symbols, a.symbols, a.published_date
        FROM articles a
        LEFT JOIN sentiment_analysis sa ON a.id = sa.article_id
        WHERE sa.article_id IS NULL
        AND a.is_deleted = FALSE
        AND a.validated_symbols IS NOT NULL
        AND JSON_LENGTH(a.validated_symbols) > 0
        ORDER BY a.published_date DESC
        LIMIT %s
        """
        return self.execute_query(query, (limit,))

    def save_sentiment_analysis(self, analysis_result: Dict) -> int:
        """Save sentiment analysis results to the database."""
        query = """
        INSERT INTO sentiment_analysis (
            article_id, sentiment_score, confidence_score,
            prediction, chunks_analyzed, metadata,
            analysis_timestamp
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            analysis_result["article_id"],
            analysis_result["sentiment_score"],
            analysis_result["confidence_score"],
            analysis_result["prediction"],
            analysis_result["chunks_analyzed"],
            json.dumps(analysis_result["metadata"]),
            analysis_result["analysis_timestamp"]
        )
        return self.execute_write(query, params)

    def get_recent_analyses(self, limit: int = 50, offset: int = 0, sort_by: str = 'analyzed') -> List[Dict]:
        """Get recent sentiment analyses with article details
        
        Args:
            limit: Number of records to return
            offset: Number of records to skip
            sort_by: Field to sort by ('analyzed' or 'published')
        """
        # Determine the ORDER BY clause based on sort_by parameter
        order_by = "sa.analysis_timestamp DESC" if sort_by == 'analyzed' else "a.published_date DESC"
        
        query = f"""
            SELECT 
                a.id as article_id,
                a.title,
                a.link,
                a.source,
                a.published_date,
                a.scraped_date,
                a.validated_symbols,
                a.content,
                sa.sentiment_score,
                sa.confidence_score,
                sa.prediction,
                sa.analysis_timestamp,
                sa.chunks_analyzed,
                sa.metadata
            FROM articles a
            JOIN sentiment_analysis sa ON a.id = sa.article_id
            WHERE a.is_deleted = FALSE
            AND a.validated_symbols IS NOT NULL
            AND JSON_LENGTH(a.validated_symbols) > 0
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """
        try:
            results = self.execute_query(query, (limit, offset))
            return results
        except Exception as e:
            logging.error(f"Error getting recent analyses: {str(e)}")
            return []

    def get_stock_sentiment_summary(self, symbol: str, hours: int = 24) -> Dict:
        """Get sentiment summary for a specific stock over the last N hours."""
        query = """
        SELECT 
            sa.sentiment_score,
            sa.confidence_score,
            sa.prediction,
            sa.analysis_timestamp,
            a.title,
            a.link
        FROM sentiment_analysis sa
        JOIN articles a ON sa.article_id = a.id
        WHERE 
            JSON_CONTAINS(a.symbols, %s, '$')
            AND sa.analysis_timestamp >= NOW() - INTERVAL %s HOUR
        ORDER BY sa.analysis_timestamp DESC
        """
        results = self.execute_query(query, (json.dumps(symbol), hours))
        
        if not results:
            return {
                "symbol": symbol,
                "error": "No sentiment data available"
            }

        # Calculate weighted average sentiment
        total_weight = 0
        weighted_sentiment = 0
        articles = []

        for result in results:
            # More recent articles get higher weight
            age_hours = (datetime.utcnow() - result["analysis_timestamp"]).total_seconds() / 3600
            weight = 1.0 / (1 + age_hours)  # Decay weight with age
            
            weighted_sentiment += result["sentiment_score"] * weight * result["confidence_score"]
            total_weight += weight
            
            articles.append({
                "title": result["title"],
                "link": result["link"],
                "sentiment": result["sentiment_score"],
                "confidence": result["confidence_score"],
                "prediction": result["prediction"],
                "timestamp": result["analysis_timestamp"].isoformat()
            })

        return {
            "symbol": symbol,
            "aggregate_sentiment": round(weighted_sentiment / total_weight, 4),
            "articles_analyzed": len(results),
            "time_window_hours": hours,
            "articles": articles
        }

    def initialize_tables(self):
        """Initialize necessary database tables"""
        try:
            # Create analyzer state table if it doesn't exist
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS analyzer_state (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    is_paused BOOLEAN DEFAULT FALSE,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            # Insert initial analyzer state if table is empty
            self.execute_query("""
                INSERT INTO analyzer_state (is_paused)
                SELECT FALSE FROM DUAL
                WHERE NOT EXISTS (SELECT 1 FROM analyzer_state)
            """)
            
            logging.info("Database tables initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing database tables: {str(e)}")
            raise

    def store_sentiment_analysis(self, article_id: int, sentiment_result: dict) -> None:
        """Store sentiment analysis results in the database"""
        query = """
            INSERT INTO sentiment_analysis 
            (article_id, sentiment_score, confidence_score, prediction, 
             chunks_analyzed, metadata, analysis_timestamp)
            VALUES (%s, %s, %s, %s, %s, %s, NOW())
        """
        
        # Extract values from the sentiment_result dictionary
        params = (
            article_id,
            sentiment_result.get('sentiment_score'),
            sentiment_result.get('confidence_score'),
            sentiment_result.get('prediction'),
            sentiment_result.get('chunks_analyzed', 1),  # Default to 1 if not provided
            json.dumps(sentiment_result.get('metadata', {}))  # Convert metadata to JSON
        )
        
        update_query = """
            UPDATE articles 
            SET is_analyzed = TRUE, 
                analyzed_at = NOW() 
            WHERE id = %s
        """
        
        try:
            # Insert sentiment analysis result
            self.execute_query(query, params)
            # Update article status
            self.execute_query(update_query, (article_id,))
            logging.info(f"Stored sentiment analysis for article {article_id}")
        except Exception as e:
            logging.error(f"Failed to store sentiment analysis for article {article_id}: {str(e)}")
            raise

    def get_last_processed_timestamp(self) -> str:
        """Get the timestamp of the last processed article"""
        result = self.execute_query("""
            SELECT MAX(analysis_timestamp) as last_processed
            FROM sentiment_analysis
            WHERE analysis_timestamp IS NOT NULL
        """)
        return result[0]['last_processed'] if result and result[0]['last_processed'] else None

    def get_unanalyzed_article_count(self) -> int:
        """Get the count of articles waiting to be analyzed"""
        result = self.execute_query("""
            SELECT COUNT(*) as count
            FROM articles a
            LEFT JOIN sentiment_analysis sa ON a.id = sa.article_id
            WHERE sa.article_id IS NULL
            AND a.is_deleted = FALSE
            AND a.validated_symbols IS NOT NULL
            AND JSON_LENGTH(a.validated_symbols) > 0
        """)
        return result[0]['count'] if result else 0

    def get_analyzer_state(self) -> bool:
        """Get the current pause state of the analyzer"""
        result = self.execute_query("SELECT is_paused FROM analyzer_state LIMIT 1")
        return result[0]['is_paused'] if result else False

    def set_analyzer_state(self, is_paused: bool) -> None:
        """Set the pause state of the analyzer"""
        self.execute_query(
            "UPDATE analyzer_state SET is_paused = %s",
            (is_paused,)
        )

    def get_stock_sentiment(self, symbol: str) -> List[Dict]:
        """Get sentiment analyses for a specific stock symbol"""
        query = """
            SELECT 
                a.title,
                a.link,
                a.published_date,
                sa.sentiment_score,
                sa.confidence_score,
                sa.prediction,
                sa.analysis_timestamp
            FROM articles a
            JOIN sentiment_analysis sa ON a.id = sa.article_id
            WHERE 
                JSON_CONTAINS(a.symbols, %s)
                AND a.is_deleted = FALSE
            ORDER BY sa.analysis_timestamp DESC
            LIMIT 50
        """
        return self.execute_query(query, (json.dumps(symbol),))

    def get_analyzed_count(self) -> int:
        """Get total count of analyzed articles with validated symbols"""
        result = self.execute_query("""
            SELECT COUNT(*) as count
            FROM sentiment_analysis sa
            JOIN articles a ON sa.article_id = a.id
            WHERE a.validated_symbols IS NOT NULL
            AND JSON_LENGTH(a.validated_symbols) > 0
        """)
        return result[0]['count'] if result else 0

    def get_sentiment_count(self, prediction: str) -> int:
        """Get count of articles with specific sentiment prediction and validated symbols"""
        result = self.execute_query("""
            SELECT COUNT(*) as count
            FROM sentiment_analysis sa
            JOIN articles a ON sa.article_id = a.id
            WHERE prediction = %s
            AND a.validated_symbols IS NOT NULL
            AND JSON_LENGTH(a.validated_symbols) > 0
        """, (prediction,))
        return result[0]['count'] if result else 0

    def get_sentiment_count_timewindow(self, prediction: str, hours: int) -> int:
        """Get count of articles with specific sentiment in the last N hours with validated symbols"""
        result = self.execute_query("""
            SELECT COUNT(*) as count
            FROM sentiment_analysis sa
            JOIN articles a ON sa.article_id = a.id
            WHERE prediction = %s
            AND a.validated_symbols IS NOT NULL
            AND JSON_LENGTH(a.validated_symbols) > 0
            AND sa.analysis_timestamp >= NOW() - INTERVAL %s HOUR
        """, (prediction, hours))
        return result[0]['count'] if result else 0

    def get_sentiment_ratio_timewindow(self, hours: int) -> dict:
        """Get bullish/bearish counts and ratio for the last N hours."""
        bullish = self.get_sentiment_count_timewindow("bullish", hours)
        bearish = self.get_sentiment_count_timewindow("bearish", hours)
        total = bullish + bearish
        ratio = bullish / total if total > 0 else 0.5
        return {"bullish": bullish, "bearish": bearish, "ratio": ratio}

    def get_sentiment_ratio_today(self) -> dict:
        """Get bullish/bearish counts and ratio for today (midnight to now)."""
        result = self.execute_query("""
            SELECT prediction, COUNT(*) as count
            FROM sentiment_analysis sa
            JOIN articles a ON sa.article_id = a.id
            WHERE a.validated_symbols IS NOT NULL
            AND JSON_LENGTH(a.validated_symbols) > 0
            AND DATE(sa.analysis_timestamp) = CURDATE()
            GROUP BY prediction
        """)
        bullish = 0
        bearish = 0
        for row in result:
            if row["prediction"] == "bullish":
                bullish = row["count"]
            elif row["prediction"] == "bearish":
                bearish = row["count"]
        total = bullish + bearish
        ratio = bullish / total if total > 0 else 0.5
        return {"bullish": bullish, "bearish": bearish, "ratio": ratio} 