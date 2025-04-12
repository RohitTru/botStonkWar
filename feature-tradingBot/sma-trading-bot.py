from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestTradeRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Position

from datetime import datetime, timedelta
from collections import deque
import time

# Alpaca credentials
API_KEY = ''
SECRET_KEY = ''

# Create clients for market data and trading
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)

# Fetch the latest trade price
def fetch_latest_price():
    # Get the latest trade (price) for the stock symbol specified below
    request = StockLatestTradeRequest(symbol_or_symbols=["AAPL"])
    latest_trade = data_client.get_stock_latest_trade(request)
    return latest_trade["AAPL"].price

# Place a market buy order
def buy(quantity):
    # Create order object
    order = MarketOrderRequest(
        symbol="AAPL",                    # Ticker symbol
        qty=quantity,                     # Number of shares
        side=OrderSide.BUY,               # Buy or sell
        time_in_force=TimeInForce.GTC     # 'day', 'gtc', 'opg', etc.
    )
    trading_client.submit_order(order)    # Submit order to the trading client

# Place a market sell order
def sell(quantity):
    # Create order object
    order = MarketOrderRequest(
        symbol="AAPL",                    # Ticker symbol
        qty=quantity,                     # Number of shares
        side=OrderSide.SELL,               # Buy or sell
        time_in_force=TimeInForce.GTC     # 'day', 'gtc', 'opg', etc.
    )
    trading_client.submit_order(order)    # Submit order to the trading client

# Main bot logic
def real_time_sma_bot():

    # Get the capital and number of stocks held from Alpaca API
    account = trading_client.get_account()
    cash_balance = float(account.cash)
    cash_to_use = 0.01 * cash_balance
    try:
        position = trading_client.get_open_position("AAPL")
        stocks_held = float(position.qty)
        position_open = True
    except Exception:
        stocks_held = 0
        position_open = False

    # Define the period size (amount of prices to be considered before calculating SMA)
    period = 20
    # Queue for holding new prices
    price_window = deque(maxlen=period) # When the deque reaches its max length oldest values are automatically discarded when new ones come in

    # Keep track of the stock prices and profit and/or loss of each trade
    price_log = []
    trade_log = []

    # Stop loss threshold to avoid holding in sharp downtrends
    stop_loss_threshold = 0.005
    entry_price = None # Need to track the entry price for stop loss threshold

    # Include a volatility threshold to ensure that trades are made only if there are significant price movements
    volatility_threshold = 0.30

    #  Add a cooldown period to prevent wash trade errors (buy and sell of the same security at nearly the same time with no meaningful change in market value)
    last_trade_time = None
    cooldown_period = timedelta(minutes=5)

    try:
        while True:
            price = fetch_latest_price()
            if price is None:
                time.sleep(60)
                continue

            # Make sure position is up to date
            try:
                position = trading_client.get_open_position("AAPL")
                stocks_held = float(position.qty)
                position_open = stocks_held > 0
            except Exception:
                position_open = False

            # Track time for cooldown period
            now = datetime.now()

            # Display the price, log the price, and append it to the price window (used for calculating the SMA)
            print(f"Price fetched: {price:.2f}")
            price_window.append(price)
            price_log.append(price)

            # Check if there are enough new price values to calculate another point on the SMA trendline
            if len(price_window) == period:
                sma = sum(price_window) / period
                volatility = max(price_window) - min(price_window)
                print(f"SMA-{period}: {sma:.2f}, Volatility: {volatility:.2f}")

                # Check if there is enough volatility
                if volatility < volatility_threshold:
                    print("Volatility too low — skipping trade.")
                    time.sleep(60)
                    continue

                # Stop loss
                if position_open and entry_price is not None:
                    # Check for stop loss
                    if price < entry_price * (1 - stop_loss_threshold):
                      if last_trade_time is None or (now - last_trade_time) > cooldown_period:
                        last_trade_time = now
                        quantity = int(stocks_held)
                        sell(quantity)
                        position_open = False
                        realized_pnl = (price - entry_price) * quantity
                        trade_log.append(realized_pnl)
                        print(f"[{now}] Stop loss triggered. Sold {quantity} shares at ${price:.2f} (P&L: {realized_pnl:.2f})")
                        entry_price = None

                # Buy (when price goes below support)
                if price < sma and not position_open:
                    if last_trade_time is None or (now - last_trade_time) > cooldown_period:
                        # Determine how much to buy
                        quantity = int(cash_to_use / price)
                        if quantity > 0:
                          last_trade_time = now
                          entry_price = price
                          buy(quantity)
                          position_open = True
                          print(f"[{now}] Bought {quantity} shares at ${price:.2f}")

                # Sell (when price rises above the resistance level)
                elif price > sma and position_open:
                    if last_trade_time is None or (now - last_trade_time) > cooldown_period:
                        try:
                            last_trade_time = now
                            position = trading_client.get_open_position("AAPL")
                            quantity = int(float(position.qty))
                            sell(quantity)
                            position_open = False
                            # If we start with a position already open then entry price will be none
                            if entry_price is not None:
                                realized_pnl = (price - entry_price) * quantity
                                trade_log.append(realized_pnl)
                                print(f"[{now}] Sold {quantity} shares at ${price:.2f} (P&L: {realized_pnl:.2f})")
                                entry_price = None
                        except Exception:
                            print("No position to sell.")
            # If there are not enough price values to caculate another point on the SMA trendline then notify the user
            else:
                print(f"Waiting for {period - len(price_window)} more data points...")

            # Make the bot wait 1 minute before it fetches the next price value
            time.sleep(60)

    # Display the closing portfolio, the open portfolio, and output the day's price log
    # Get account info
    finally:
        # Get account information
        account = trading_client.get_account()
        print("\n=== ACCOUNT SUMMARY ===")
        print(f"Cash: ${float(account.cash):,.2f}")
        print(f"Buying Power: ${float(account.buying_power):,.2f}")
        print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"Price Log: {price_log}\n")

        # Get stock positions
        positions = trading_client.get_all_positions()
        print("=== STOCK HOLDINGS ===")
        for pos in positions:
            print(f"{pos.symbol}: {pos.qty} shares @ ${float(pos.current_price):.2f}")

        # Calculate net profit/loss
        net_pnl = sum(trade_log)
        print("\n=== TRADE SUMMARY ===")
        print(f"Number of trades: {len(trade_log)}")
        print(f"Net P&L: ${net_pnl:.2f}")
        print("P&L per trade:", [f"${p:.2f}" for p in trade_log])

# Run the trading bot
real_time_sma_bot()
