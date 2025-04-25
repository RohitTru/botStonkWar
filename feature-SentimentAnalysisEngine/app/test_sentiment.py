import logging
from database import Database
from sentiment_analyzer import SentimentAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_sentiment_pipeline():
    try:
        # Initialize components
        db = Database()
        analyzer = SentimentAnalyzer()
        
        # Get unanalyzed articles
        logging.info("Fetching unanalyzed articles...")
        articles = db.get_unanalyzed_articles(limit=5)
        logging.info(f"Found {len(articles)} unanalyzed articles")
        
        if not articles:
            logging.info("No unanalyzed articles found")
            return
        
        # Process each article
        for article in articles:
            try:
                logging.info(f"\nProcessing article ID: {article['id']}")
                logging.info(f"Title: {article['title']}")
                
                # Prepare article data
                article_data = {
                    "id": article["id"],
                    "text": article["content"],
                    "stock_symbol": article["symbols"]
                }
                
                # Run sentiment analysis
                analysis = analyzer.analyze_article(article["content"], article_data)
                
                if "error" in analysis:
                    logging.error(f"Analysis failed: {analysis['error']}")
                    continue
                
                # Log analysis results
                logging.info(f"Sentiment Score: {analysis['sentiment_score']}")
                logging.info(f"Confidence Score: {analysis['confidence_score']}")
                logging.info(f"Prediction: {analysis['prediction']}")
                logging.info(f"Chunks Analyzed: {analysis['chunks_analyzed']}")
                
                # Save to database
                db.save_sentiment_analysis(analysis)
                logging.info("Analysis saved to database successfully")
                
            except Exception as e:
                logging.error(f"Error processing article {article['id']}: {str(e)}")
                continue
        
        # Test retrieving recent analyses
        logging.info("\nFetching recent analyses...")
        recent = db.get_recent_analyses(limit=5)
        logging.info(f"Retrieved {len(recent)} recent analyses")
        
        for analysis in recent:
            logging.info(f"\nArticle: {analysis['title']}")
            logging.info(f"Sentiment: {analysis['sentiment_score']}")
            logging.info(f"Prediction: {analysis['prediction']}")
            
    except Exception as e:
        logging.error(f"Test failed: {str(e)}")

if __name__ == "__main__":
    logging.info("Starting sentiment analysis pipeline test...")
    test_sentiment_pipeline()
    logging.info("Test complete") 