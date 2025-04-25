from typing import List, Dict, Any
import logging
from datetime import datetime
from database import Database
from sentiment_analyzer import SentimentAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalyzerManager:
    def __init__(self, db: Database):
        self.db = db
        self.analyzer = SentimentAnalyzer()
        self._initialize()

    def _initialize(self):
        """Initialize the analyzer manager"""
        self.db.initialize_tables()
        logger.info("Analyzer manager initialized")

    def is_paused(self) -> bool:
        """Check if the analyzer is paused"""
        return self.db.get_analyzer_state()

    def pause(self) -> None:
        """Pause the analyzer"""
        self.db.set_analyzer_state(True)
        logger.info("Analyzer paused")

    def resume(self) -> None:
        """Resume the analyzer"""
        self.db.set_analyzer_state(False)
        logger.info("Analyzer resumed")

    def process_pending_articles(self) -> int:
        """Process any pending articles if not paused"""
        if self.is_paused():
            logger.info("Analyzer is paused, skipping processing")
            return 0

        try:
            # Get unanalyzed articles
            articles = self.db.get_unanalyzed_articles()
            if not articles:
                return 0

            processed_count = 0
            for article in articles:
                try:
                    # Perform sentiment analysis
                    sentiment_result = self.analyzer.analyze_article(
                        article_text=article['content'],
                        article_metadata={
                            'id': article['id'],
                            'title': article['title'],
                            'link': article.get('link', '')
                        }
                    )

                    # Store the analysis results
                    if 'error' not in sentiment_result:
                        # Make sure we have all required fields
                        if not all(k in sentiment_result for k in ['sentiment_score', 'confidence_score', 'prediction']):
                            logger.error(f"Missing required fields in sentiment result for article {article['id']}")
                            continue
                            
                        self.db.store_sentiment_analysis(
                            article_id=article['id'],
                            sentiment_result=sentiment_result
                        )
                        processed_count += 1
                        logger.info(f"Successfully analyzed article {article['id']}")
                    else:
                        logger.error(f"Error analyzing article {article['id']}: {sentiment_result['error']}")

                except Exception as e:
                    logger.error(f"Error processing article {article['id']}: {str(e)}")
                    continue

            logger.info(f"Processed {processed_count} articles")
            return processed_count

        except Exception as e:
            logger.error(f"Error in process_pending_articles: {str(e)}")
            return 0

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the analyzer"""
        return {
            "is_paused": self.is_paused(),
            "last_processed": self.db.get_last_processed_timestamp(),
            "pending_count": self.db.get_unanalyzed_article_count()
        } 