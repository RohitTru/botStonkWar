"""
Ticker validator implementation that integrates with the database and yfinance.
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime, timedelta
import yfinance as yf
import json
from app.utils.logging import setup_logger
import time
import os

logger = setup_logger()

class TickerValidator:
    """A modular ticker validator that uses database caching and yfinance validation."""
    
    def __init__(self, db_connection):
        """
        Initialize the validator.
        
        Args:
            db_connection: Database connection to use for ticker validation
        """
        self.db = db_connection
        
        # Common words that shouldn't be considered as tickers
        self.common_words = {
            'THE', 'AND', 'FOR', 'NEW', 'INC', 'LTD', 'LLC', 'CORP',
            'CEO', 'CFO', 'CTO', 'COO', 'NYSE', 'IPO', 'ETF', 'USA',
            'GDP', 'FBI', 'SEC', 'FED', 'USD', 'CEO', 'AI', 'US',
            'Q1', 'Q2', 'Q3', 'Q4', 'YOY', 'QOQ', 'EST', 'PST',
            'EDT', 'PDT', 'GMT', 'PM', 'AM', 'NEWS', 'UPDATE'
        }
        
        # Company name to symbol mapping cache
        self.company_to_symbol = {}
        
        # Rate limiting parameters
        self.last_api_call = 0
        self.min_api_interval = 0.2  # Minimum 200ms between API calls
        
        # Load ticker data from JSON
        tickers_path = os.path.join(os.path.dirname(__file__), 'company_tickers.json')
        with open(tickers_path, 'r') as f:
            tickers_data = json.load(f)
        self.valid_tickers = {entry['ticker'] for entry in tickers_data.values()}
        self.ticker_to_company = {entry['ticker']: entry['title'] for entry in tickers_data.values()}
        self.company_to_ticker = {entry['title'].upper(): entry['ticker'] for entry in tickers_data.values()}
        
    def _rate_limit(self):
        """Implement rate limiting for API calls."""
        current_time = time.time()
        time_since_last = current_time - self.last_api_call
        if time_since_last < self.min_api_interval:
            time.sleep(self.min_api_interval - time_since_last)
        self.last_api_call = time.time()

    def _check_cache(self, symbol: str) -> Optional[Dict]:
        """Check if symbol exists in database cache."""
        try:
            query = """
                SELECT symbol, exchange, company_name, is_active, last_verified
                FROM ticker_symbols
                WHERE symbol = %s AND is_active = TRUE
                AND last_verified > DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            result = self.db.execute_query(query, (symbol,))
            
            if result and len(result) > 0:
                ticker_data = result[0]
                return {
                    'symbol': ticker_data['symbol'],
                    'exchange': ticker_data['exchange'],
                    'company_name': ticker_data['company_name'],
                    'validated': True,
                    'last_verified': ticker_data['last_verified'].isoformat()
                }
            return None
            
        except Exception as e:
            logger.error(f"Error checking ticker cache: {e}")
            return None

    def _update_cache(self, symbol: str, info: Dict) -> None:
        """Update the ticker symbols cache."""
        try:
            query = """
                INSERT INTO ticker_symbols 
                    (symbol, exchange, company_name, is_active, last_verified)
                VALUES (%s, %s, %s, %s, NOW())
                ON DUPLICATE KEY UPDATE
                    exchange = VALUES(exchange),
                    company_name = VALUES(company_name),
                    is_active = VALUES(is_active),
                    last_verified = NOW()
            """
            params = (
                symbol,
                info.get('exchange', ''),
                info.get('longName', info.get('shortName', '')),
                True
            )
            self.db.execute_query(query, params)
            
        except Exception as e:
            logger.error(f"Error updating ticker cache: {e}")

    def validate_symbol(self, symbol: str) -> Dict:
        """
        Validate a single symbol using cache and yfinance.
        
        Args:
            symbol: The ticker symbol to validate
            
        Returns:
            Dictionary containing validation result
        """
        # Clean the symbol
        symbol = symbol.strip().upper()
        
        # Check common words
        if symbol in self.common_words:
            return {'symbol': symbol, 'validated': False, 'reason': 'common_word'}
            
        # Check cache first
        cache_result = self._check_cache(symbol)
        if cache_result:
            return cache_result
            
        try:
            # Rate limiting
            self._rate_limit()
            
            # Use yfinance to validate
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if info and 'regularMarketPrice' in info:
                # Valid symbol found
                result = {
                    'symbol': symbol,
                    'exchange': info.get('exchange', ''),
                    'company_name': info.get('longName', info.get('shortName', '')),
                    'validated': True,
                    'last_verified': datetime.now().isoformat()
                }
                
                # Update cache
                self._update_cache(symbol, info)
                
                return result
            else:
                return {'symbol': symbol, 'validated': False, 'reason': 'not_found'}
                
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return {'symbol': symbol, 'validated': False, 'reason': str(e)}

    def validate_symbols(self, symbols: List[str]) -> List[Dict]:
        """
        Validate multiple symbols.
        
        Args:
            symbols: List of symbols to validate
            
        Returns:
            List of validation results
        """
        return [self.validate_symbol(symbol) for symbol in symbols]

    def extract_symbols(self, text: str) -> List[str]:
        """
        Extract potential symbols from text.
        
        Args:
            text: Text to extract symbols from
            
        Returns:
            List of potential symbols
        """
        return set(re.findall(r'\b[A-Z]{1,5}\b', text))

    def extract_company_names(self, text: str) -> Set[str]:
        """
        Extract company names from text.
        
        Args:
            text: Text to extract company names from
            
        Returns:
            Set of company names
        """
        found = set()
        upper_text = text.upper()
        for name, ticker in self.company_to_ticker.items():
            if name in upper_text:
                found.add(ticker)
        return found

    def process_article_symbols(self, article_data: Dict) -> Tuple[List[Dict], List[Dict]]:
        """
        Process and validate symbols from an article.
        
        Args:
            article_data: Article data containing title and content
            
        Returns:
            Tuple of (all_symbols, validated_symbols)
        """
        # Extract symbols from title and content
        text = f"{article_data.get('title', '')} {article_data.get('content', '')}"
        symbols = self.extract_symbols(text)
        
        # Validate each symbol
        all_symbols = []
        validated_symbols = []
        
        for symbol in symbols:
            result = self.validate_symbol(symbol)
            all_symbols.append(result)
            if result['validated']:
                validated_symbols.append(result)
        
        # Add tickers found by company name
        validated_symbols |= self.extract_company_names(text)
        
        return all_symbols, validated_symbols

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