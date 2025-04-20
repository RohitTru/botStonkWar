from app.scrapers.base import BaseScraper
import yfinance as yf
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import re

class YahooFinanceScraper(BaseScraper):
    def __init__(self):
        super().__init__('yahoo_finance')
        self.base_url = "https://finance.yahoo.com/news"
    
    def get_articles(self):
        """Get articles from Yahoo Finance."""
        try:
            # Fetch the news page
            response = self.session.get(self.base_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            # Find all news articles
            for article in soup.find_all('div', {'class': 'Ov(h)'}):
                try:
                    link = article.find('a')
                    if not link:
                        continue
                        
                    url = f"https://finance.yahoo.com{link['href']}" if link['href'].startswith('/') else link['href']
                    title = link.text.strip()
                    
                    # Get article timestamp if available
                    time_element = article.find('span', {'class': 'C($c-fuji-grey-j)'})
                    published_at = datetime.now()  # Default to now if no timestamp found
                    if time_element:
                        try:
                            # Parse the relative time text (e.g., "2 hours ago", "1 day ago")
                            time_text = time_element.text.strip()
                            # You might want to implement more sophisticated time parsing here
                            published_at = datetime.now()  # For now, using current time
                        except Exception as e:
                            self.logger.warning(f"Error parsing time for article {title}: {str(e)}")
                    
                    articles.append({
                        'url': url,
                        'title': title,
                        'source': 'Yahoo Finance',
                        'published_at': published_at
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error processing article element: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(articles)} articles from Yahoo Finance")
            return articles
            
        except Exception as e:
            self.logger.error(f"Error fetching Yahoo Finance articles: {str(e)}")
            return []
            
    def extract_stock_symbols(self, text):
        """Extract stock symbols from text using regex pattern."""
        # Look for stock symbols in parentheses (e.g., (AAPL), (GOOGL))
        pattern = r'\(([A-Z]{1,5})\)'
        matches = re.findall(pattern, text)
        
        # Also look for common stock symbol patterns
        pattern2 = r'\b[A-Z]{1,5}\b'  # 1-5 uppercase letters
        potential_symbols = re.findall(pattern2, text)
        
        # Verify symbols using yfinance
        verified_symbols = set()
        for symbol in set(matches + potential_symbols):
            try:
                ticker = yf.Ticker(symbol)
                # Try to get basic info to verify it's a valid symbol
                if ticker.info:
                    verified_symbols.add(symbol)
            except:
                continue
                
        return list(verified_symbols) 