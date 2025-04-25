from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import logging
from typing import List, Dict, Union, Optional
from datetime import datetime

class SentimentAnalyzer:
    def __init__(self):
        self.model_name = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
        self.max_tokens = 512
        
        logging.info(f"Loading sentiment model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.sentiment_pipeline = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer)
        logging.info("Sentiment model loaded successfully")

    def chunk_text(self, text: str) -> List[str]:
        """Break text into chunks that fit within model's max token limit."""
        words = text.split()
        chunks, current_chunk, length = [], [], 0

        for word in words:
            token_len = len(self.tokenizer.tokenize(word))
            if length + token_len > self.max_tokens:
                chunks.append(" ".join(current_chunk))
                current_chunk, length = [word], token_len
            else:
                current_chunk.append(word)
                length += token_len
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def analyze_article(self, article_text: str, article_metadata: Dict) -> Dict:
        """
        Analyze sentiment of an article and return detailed results.
        
        Args:
            article_text: The full text of the article
            article_metadata: Dictionary containing article metadata (title, url, etc.)
            
        Returns:
            Dictionary containing sentiment analysis results
        """
        try:
            # Break article into chunks
            chunks = self.chunk_text(article_text)
            if not chunks:
                raise ValueError("No valid text chunks found in article")

            # Analyze each chunk
            chunk_sentiments = self.sentiment_pipeline(chunks)
            
            # Convert to signed scores (-1 to 1 range)
            signed_scores = [
                s["score"] if s["label"] == "positive" else -s["score"]
                for s in chunk_sentiments
            ]

            # Calculate overall sentiment
            avg_sentiment = sum(signed_scores) / len(signed_scores)
            
            # Determine confidence level based on consistency of chunks
            sentiment_variance = sum((s - avg_sentiment) ** 2 for s in signed_scores) / len(signed_scores)
            confidence_score = 1 / (1 + sentiment_variance)  # Higher variance = lower confidence

            return {
                "article_id": article_metadata.get("id"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "sentiment_score": round(avg_sentiment, 4),
                "confidence_score": round(confidence_score, 4),
                "prediction": "bullish" if avg_sentiment > 0 else "bearish",
                "chunks_analyzed": len(chunks),
                "metadata": {
                    "model": self.model_name,
                    "chunk_scores": [round(score, 4) for score in signed_scores],
                    "variance": round(sentiment_variance, 4)
                }
            }

        except Exception as e:
            logging.error(f"Error analyzing article: {str(e)}")
            return {
                "article_id": article_metadata.get("id"),
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "failed"
            }

    def analyze_stock_sentiment(self, articles: List[Dict]) -> Dict:
        """
        Analyze multiple articles about a stock and provide aggregated sentiment.
        
        Args:
            articles: List of dictionaries containing article text and metadata
            
        Returns:
            Dictionary containing aggregated sentiment analysis for the stock
        """
        if not articles:
            return {"error": "No articles provided for analysis"}

        stock_symbol = articles[0].get("stock_symbol")
        analysis_results = []
        
        for article in articles:
            result = self.analyze_article(article["text"], article)
            if "error" not in result:
                analysis_results.append(result)

        if not analysis_results:
            return {
                "stock_symbol": stock_symbol,
                "timestamp": datetime.utcnow().isoformat(),
                "error": "No successful article analyses"
            }

        # Weight recent articles more heavily
        total_weight = 0
        weighted_sentiment = 0
        
        for i, result in enumerate(analysis_results):
            # More recent articles get higher weights
            weight = 1.0 / (i + 1)  # 1, 1/2, 1/3, etc.
            total_weight += weight
            weighted_sentiment += result["sentiment_score"] * weight * result["confidence_score"]

        final_sentiment = weighted_sentiment / total_weight

        return {
            "stock_symbol": stock_symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "aggregate_sentiment": round(final_sentiment, 4),
            "prediction": "bullish" if final_sentiment > 0 else "bearish",
            "confidence": round(sum(r["confidence_score"] for r in analysis_results) / len(analysis_results), 4),
            "articles_analyzed": len(analysis_results),
            "individual_results": analysis_results
        } 