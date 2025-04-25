"""
Ticker validator implementation that integrates with the database.
"""

import re
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
import mysql.connector
from app.utils.logging import setup_logger

logger = setup_logger()

class TickerValidator:
    """A modular ticker validator that uses database-backed validation."""
    
    def __init__(self, db_connection):
        """
        Initialize the validator.
        
        Args:
            db_connection: Database connection to use for ticker validation
        """
        self.db = db_connection
        
        # Basic validation rules
        self.min_length = 1
        self.max_length = 10  # Increased to match DB schema
        self.valid_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ-.")  # Added - and . for tickers like BRK-B
        
        # Common words that shouldn't be considered as tickers
        self.common_words = {
            'THE', 'AND', 'FOR', 'NEW', 'INC', 'LTD', 'LLC', 'CORP',
            'CEO', 'CFO', 'CTO', 'COO', 'NYSE', 'IPO', 'ETF'
        }
        
        # Cache for validation results
        self._cache = {}
        
    def validate_ticker(self, ticker: str, context: Optional[Dict] = None) -> Dict:
        """
        Validate a single ticker symbol.
        
        Args:
            ticker: The ticker symbol to validate
            context: Optional dictionary with article context (title, content)
            
        Returns:
            Dictionary containing validation result
        """
        # Normalize ticker
        ticker = ticker.strip().upper()
        
        # Check cache
        cache_key = f"{ticker}:{hash(str(context))}"
        if cache_key in self._cache:
            return self._cache[cache_key]
            
        result = {
            'ticker': ticker,
            'is_valid': False,
            'reason': None,
            'metadata': {},
            'confidence': 0.0,
            'validated_at': datetime.utcnow().isoformat()
        }
        
        # Basic format validation
        if len(ticker) < self.min_length:
            result['reason'] = 'too_short'
            return self._cache_result(cache_key, result)
            
        if len(ticker) > self.max_length:
            result['reason'] = 'too_long'
            return self._cache_result(cache_key, result)
            
        # Character validation
        invalid_chars = set(ticker) - self.valid_chars
        if invalid_chars:
            result['reason'] = f'invalid_chars: {invalid_chars}'
            return self._cache_result(cache_key, result)
            
        # Common word check
        if ticker in self.common_words:
            result['reason'] = 'common_word'
            return self._cache_result(cache_key, result)
            
        # Check if ticker exists in database
        ticker_info = self._check_ticker_exists(ticker)
        if ticker_info:
            result['is_valid'] = True
            result['metadata'] = ticker_info
            result['confidence'] = 1.0
        else:
            # If ticker not in database, validate against context
            if context:
                confidence = self._validate_context(ticker, context)
                result['confidence'] = confidence
                if confidence > 0.7:  # High confidence threshold
                    result['is_valid'] = True
                    # Could potentially add to ticker_symbols table here
                else:
                    result['reason'] = 'no_context_match'
            else:
                result['reason'] = 'not_in_database'
                
        return self._cache_result(cache_key, result)
        
    def _check_ticker_exists(self, ticker: str) -> Optional[Dict]:
        """Check if ticker exists in the ticker_symbols table."""
        try:
            query = """
                SELECT symbol, exchange, company_name, is_active, last_verified
                FROM ticker_symbols
                WHERE symbol = %s AND is_active = TRUE
            """
            result = self.db.execute_query(query, (ticker,))
            
            if result and len(result) > 0:
                ticker_data = result[0]
                return {
                    'symbol': ticker_data['symbol'],
                    'exchange': ticker_data['exchange'],
                    'company_name': ticker_data['company_name'],
                    'last_verified': ticker_data['last_verified'].isoformat()
                }
            return None
            
        except Exception as e:
            logger.error(f"Error checking ticker existence: {e}")
            return None
        
    def _validate_context(self, ticker: str, context: Dict) -> float:
        """
        Validate ticker against article context.
        Returns confidence score between 0 and 1.
        """
        title = context.get('title', '').upper()
        content = context.get('content', '').upper()
        
        confidence = 0.0
        
        # Check direct mentions
        if ticker in title:
            confidence = max(confidence, 0.9)  # High confidence for title matches
        if ticker in content:
            confidence = max(confidence, 0.7)  # Good confidence for content matches
            
        # Check common stock symbol formats
        patterns = [
            f"${ticker}",      # $AAPL
            f"({ticker})",     # (AAPL)
            f"NYSE:{ticker}",  # NYSE:AAPL
            f"NASDAQ:{ticker}" # NASDAQ:AAPL
        ]
        
        for pattern in patterns:
            if pattern in title:
                confidence = max(confidence, 0.95)
            if pattern in content:
                confidence = max(confidence, 0.8)
                
        return confidence
        
    def _cache_result(self, cache_key: str, result: Dict) -> Dict:
        """Cache and return the validation result."""
        self._cache[cache_key] = result
        return result
        
    def validate_tickers(self, tickers: List[str], context: Optional[Dict] = None) -> Dict[str, Dict]:
        """
        Validate multiple ticker symbols.
        
        Args:
            tickers: List of ticker symbols to validate
            context: Optional dictionary with article context
            
        Returns:
            Dictionary mapping tickers to their validation results
        """
        return {
            ticker: self.validate_ticker(ticker, context)
            for ticker in tickers
        }
        
    def get_stats(self) -> Dict:
        """Get validator statistics."""
        total = len(self._cache)
        valid = sum(1 for result in self._cache.values() if result['is_valid'])
        
        return {
            'total_validations': total,
            'valid_count': valid,
            'invalid_count': total - valid,
            'cache_size': total
        }
        
    def add_valid_ticker(self, symbol: str, exchange: str, company_name: str) -> bool:
        """
        Add a new valid ticker to the database.
        
        Args:
            symbol: The ticker symbol
            exchange: The exchange where the ticker is traded
            company_name: The company name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            query = """
                INSERT INTO ticker_symbols (symbol, exchange, company_name)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    exchange = VALUES(exchange),
                    company_name = VALUES(company_name),
                    is_active = TRUE,
                    last_verified = CURRENT_TIMESTAMP
            """
            self.db.execute_query(query, (symbol, exchange, company_name))
            return True
        except Exception as e:
            logger.error(f"Error adding valid ticker: {e}")
            return False 