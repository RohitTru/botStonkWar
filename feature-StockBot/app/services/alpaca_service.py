import os
from alpaca_trade_api.rest import REST, TimeFrame

class AlpacaService:
    def __init__(self):
        self.api_key = os.getenv('ALPACA_KEY')
        self.api_secret = os.getenv('ALPACA_SECRET')
        self.base_url = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
        self.api = REST(self.api_key, self.api_secret, self.base_url)

    def submit_order(self, symbol, qty, side, type='market', time_in_force='gtc'):
        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force=time_in_force
        )

    def get_latest_price(self, symbol):
        barset = self.api.get_bars(symbol, TimeFrame.Minute, limit=1)
        if barset:
            return float(barset[0].c)
        return None 