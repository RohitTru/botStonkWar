import threading
import websocket
import json
import time
import os

class AlpacaWebSocketPriceService:
    def __init__(self, symbols):
        self.api_key = os.getenv('ALPACA_KEY')
        self.api_secret = os.getenv('ALPACA_SECRET')
        self.feed = 'iex'  # or 'sip' if you have access
        self.url = f"wss://stream.data.alpaca.markets/v2/{self.feed}"
        self.symbols = set(symbols)
        self.price_cache = {}  # symbol -> latest price dict
        self.ws = None
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def _run(self):
        def on_message(ws, message):
            data = json.loads(message)
            if isinstance(data, dict):
                data = [data]
            for msg in data:
                if msg.get('T') == 't':  # trade
                    symbol = msg['S']
                    price = msg['p']
                    self.price_cache[symbol] = {
                        'price': price,
                        'last_updated': msg['t'],
                        'status': 'ok'
                    }
        def on_open(ws):
            auth_msg = {
                "action": "auth",
                "key": self.api_key,
                "secret": self.api_secret
            }
            ws.send(json.dumps(auth_msg))
            time.sleep(1)
            sub_msg = {
                "action": "subscribe",
                "trades": list(self.symbols),
                "quotes": list(self.symbols)
            }
            ws.send(json.dumps(sub_msg))
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=on_open,
            on_message=on_message
        )
        self.ws.run_forever()

    def get_price(self, symbol):
        return self.price_cache.get(symbol)

    def add_symbol(self, symbol):
        if symbol not in self.symbols:
            self.symbols.add(symbol)
            # Re-subscribe logic can be added here if needed 