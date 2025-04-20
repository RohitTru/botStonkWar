from app.models import db, Stock
import logging

logger = logging.getLogger(__name__)

class StockService:
    def __init__(self):
        self.logger = logger

    def get_or_create_stock(self, symbol, name=None):
        """Get a stock by symbol or create it if it doesn't exist."""
        try:
            stock = Stock.query.filter_by(symbol=symbol).first()
            if not stock:
                stock = Stock(symbol=symbol, name=name)
                db.session.add(stock)
                db.session.commit()
                self.logger.info(f"Created new stock: {symbol}")
            return stock
        except Exception as e:
            self.logger.error(f"Error getting/creating stock {symbol}: {str(e)}")
            db.session.rollback()
            return None

    def get_stock_by_id(self, stock_id):
        """Get a stock by its ID."""
        try:
            return Stock.query.get(stock_id)
        except Exception as e:
            self.logger.error(f"Error getting stock by ID {stock_id}: {str(e)}")
            return None

    def get_all_stocks(self):
        """Get all stocks."""
        try:
            return Stock.query.all()
        except Exception as e:
            self.logger.error(f"Error getting all stocks: {str(e)}")
            return [] 