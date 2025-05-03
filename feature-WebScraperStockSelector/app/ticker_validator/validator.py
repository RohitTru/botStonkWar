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
        Extract potential symbols from text with improved filtering.
        
        Args:
            text: Text to extract symbols from
            
        Returns:
            Set of potential symbols
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
                potential_symbols.add(symbol)
        
        # Filter out common words and single letters
        filtered_symbols = {
            symbol for symbol in potential_symbols
            if symbol not in self.common_words
            and len(symbol) > 1  # Filter out single letters
            and symbol in self.valid_tickers  # Only keep symbols we know exist
        }
        
        return filtered_symbols

    def extract_company_names(self, text: str) -> Set[str]:
        """
        Extract company names from text with improved matching.
        
        Args:
            text: Text to extract company names from
            
        Returns:
            Set of company names
        """
        found = set()
        upper_text = text.upper()
        
        # First try exact matches
        for name, ticker in self.company_to_ticker.items():
            if name in upper_text:
                found.add(ticker)
        
        # Then try partial matches for longer company names
        for name, ticker in self.company_to_ticker.items():
            if len(name.split()) > 2:  # Only for longer company names
                name_parts = name.split()
                # Check if all parts of the company name are present in the text
                if all(part in upper_text for part in name_parts):
                    found.add(ticker)
        
        return found

    def process_article_symbols(self, article_data: Dict) -> Tuple[List[Dict], List[str]]:
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
        validated_symbols = set()
        
        for symbol in symbols:
            result = self.validate_symbol(symbol)
            all_symbols.append(result)
            if result['validated']:
                validated_symbols.add(result['symbol'])
        
        # Add tickers found by company name, but only if they're valid
        company_tickers = self.extract_company_names(text)
        for ticker in company_tickers:
            result = self.validate_symbol(ticker)
            if result['validated']:
                validated_symbols.add(result['symbol'])
                # Only add to all_symbols if not already present
                if not any(s['symbol'] == result['symbol'] for s in all_symbols):
                    all_symbols.append(result)
        
        return all_symbols, list(validated_symbols) 