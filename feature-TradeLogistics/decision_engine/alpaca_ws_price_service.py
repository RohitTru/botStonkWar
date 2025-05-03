import threading
import websocket
import json
import time
import os
from collections import deque

class AlpacaWebSocketPriceService:
    def __init__(self, symbols, max_symbols=30):
        self.api_key = os.getenv('ALPACA_KEY')
        self.api_secret = os.getenv('ALPACA_SECRET')
        self.feed = 'iex'  # or 'sip' if you have access
        self.url = f"wss://stream.data.alpaca.markets/v2/{self.feed}"
        self.max_symbols = max_symbols
        self.symbols = deque(symbols[:max_symbols], maxlen=max_symbols)  # maintain order for LRU
        self.price_cache = {}  # symbol -> latest price dict
        self.ws = None
        self.ws_lock = threading.Lock()
        self._ws_ready = threading.Event()
        self._start_ws_thread()

    def _start_ws_thread(self):
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self._ws_ready.wait(timeout=10)

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
            self._ws_ready.set()
        def on_close(ws, close_status_code, close_msg):
            print(f"[AlpacaWS] Connection closed: {close_status_code} {close_msg}")
        self.ws = websocket.WebSocketApp(
            self.url,
            on_open=on_open,
            on_message=on_message,
            on_close=on_close
        )
        self.ws.run_forever()

    def get_price(self, symbol):
        return self.price_cache.get(symbol)

    def get_subscribed_symbols(self):
        return list(self.symbols)

    def subscribe(self, symbol):
        with self.ws_lock:
            if symbol in self.symbols:
                return True
            if len(self.symbols) >= self.max_symbols:
                # Remove the oldest (LRU)
                to_remove = self.symbols.popleft()
                unsub_msg = {"action": "unsubscribe", "trades": [to_remove], "quotes": [to_remove]}
                self.ws.send(json.dumps(unsub_msg))
            self.symbols.append(symbol)
            sub_msg = {"action": "subscribe", "trades": [symbol], "quotes": [symbol]}
            self.ws.send(json.dumps(sub_msg))
            return True

    def unsubscribe(self, symbol):
        with self.ws_lock:
            if symbol in self.symbols:
                self.symbols.remove(symbol)
                unsub_msg = {"action": "unsubscribe", "trades": [symbol], "quotes": [symbol]}
                self.ws.send(json.dumps(unsub_msg))
                return True
            return False

# Load tickers from company_tickers.json
COMPANY_TICKERS_PATH = os.path.join(os.path.dirname(__file__), '../../company_tickers.json')
if os.path.exists(COMPANY_TICKERS_PATH):
    with open(COMPANY_TICKERS_PATH, 'r') as f:
        data = json.load(f)
    ALL_TICKERS = [entry['ticker'] for entry in data.values()]
else:
    ALL_TICKERS = ['AAPL', 'TSLA', 'GOOG', 'MSFT', 'AMZN']

# Start with the first 5, can be empty or smarter
price_service = AlpacaWebSocketPriceService(ALL_TICKERS[:5]) 