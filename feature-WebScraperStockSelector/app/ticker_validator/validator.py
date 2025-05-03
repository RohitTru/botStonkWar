"""
Ticker validator implementation that uses company_tickers.json for validation.
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple
from datetime import datetime
import json
from app.utils.logging import setup_logger
import os

logger = setup_logger()

class TickerValidator:
    """A modular ticker validator that uses company_tickers.json for validation."""
    
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
        
        # Load ticker data from JSON
        tickers_path = os.path.join(os.path.dirname(__file__), 'company_tickers.json')
        with open(tickers_path, 'r') as f:
            tickers_data = json.load(f)
            
        # Create lookup dictionaries
        self.valid_tickers = {entry['ticker'] for entry in tickers_data.values()}
        self.ticker_to_company = {entry['ticker']: entry['title'] for entry in tickers_data.values()}
        self.company_to_ticker = {entry['title'].upper(): entry['ticker'] for entry in tickers_data.values()}

    def validate_symbol(self, symbol: str) -> Dict:
        """
        Validate a single symbol using company_tickers.json.
        
        Args:
            symbol: The ticker symbol to validate
            
        Returns:
            Dictionary containing validation result
        """
        # Clean the symbol
        symbol = symbol.strip().upper()
        
        # Quick validation checks
        if symbol in self.common_words or len(symbol) <= 1:
            return {'symbol': symbol, 'validated': False, 'reason': 'invalid_format'}
            
        # Check if symbol exists in our known valid tickers
        if symbol in self.valid_tickers:
            return {
                'symbol': symbol,
                'company_name': self.ticker_to_company.get(symbol, ''),
                'validated': True,
                'last_verified': datetime.now().isoformat()
            }
        else:
            return {'symbol': symbol, 'validated': False, 'reason': 'not_in_database'}

    def extract_symbols(self, text: str) -> Set[str]:
        """
        Extract potential symbols from text.
        
        Args:
            text: Text to extract symbols from
            
        Returns:
            Set of potential symbols found in text
        """
        # Find all potential symbols using multiple patterns
        patterns = [
            r'\b[A-Z]{1,5}\b',  # Basic ticker format
            r'\$([A-Z]{1,5})\b',  # $AAPL format
            r'NYSE:([A-Z]{1,5})\b',  # NYSE:AAPL format
            r'NASDAQ:([A-Z]{1,5})\b',  # NASDAQ:AAPL format
            r'\(([A-Z]{1,5})\)',  # (AAPL) format
            r'([A-Z]{1,5})\.(?:US|UK|CA|DE|FR|JP|AU)\b'  # AAPL.US format
        ]
        
        potential_symbols = set()
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # Extract the symbol from the match group if it exists
                symbol = match.group(1) if match.groups() else match.group(0)
                # Only filter out common words and single letters
                if symbol not in self.common_words and len(symbol) > 1:
                    potential_symbols.add(symbol)
        
        return potential_symbols

    def extract_company_names(self, text: str) -> Set[str]:
        """
        Extract company names from text with improved matching.
        
        Args:
            text: Text to extract company names from
            
        Returns:
            Set of validated ticker symbols found from company names
        """
        found = set()
        upper_text = text.upper()
        
        # First try exact matches
        for name, ticker in self.company_to_ticker.items():
            if name in upper_text and ticker in self.valid_tickers:
                found.add(ticker)
        
        # Then try partial matches for longer company names
        for name, ticker in self.company_to_ticker.items():
            if len(name.split()) > 2 and ticker in self.valid_tickers:  # Only for longer company names
                name_parts = name.split()
                # Check if all parts of the company name are present in the text
                if all(part in upper_text for part in name_parts):
                    found.add(ticker)
        
        return found

    def process_article_symbols(self, article_data: Dict) -> Tuple[List[str], List[str]]:
        """
        Process and validate symbols from an article.
        
        Args:
            article_data: Article data containing title and content
            
        Returns:
            Tuple of (all_symbols, validated_symbols)
            all_symbols: List of all symbols found in the text
            validated_symbols: List of symbols that were validated against company_tickers.json
        """
        # Extract symbols from title and content
        text = f"{article_data.get('title', '')} {article_data.get('content', '')}"
        all_symbols = list(self.extract_symbols(text))
        validated_symbols = []
        
        # Validate each symbol
        for symbol in all_symbols:
            result = self.validate_symbol(symbol)
            if result['validated']:
                validated_symbols.append(symbol)
        
        # Add tickers found by company name, but only if they're valid
        company_tickers = self.extract_company_names(text)
        for ticker in company_tickers:
            result = self.validate_symbol(ticker)
            if result['validated'] and ticker not in validated_symbols:
                validated_symbols.append(ticker)
                if ticker not in all_symbols:
                    all_symbols.append(ticker)
        
        return all_symbols, validated_symbols 