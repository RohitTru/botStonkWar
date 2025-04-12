SMA-trading-bot.py is a real-time stock trading bot that uses the concept of mean reversion along with a Simple Moving Average (SMA) strategy to trade a specified stock using the Alpaca API. The bot monitors live stock prices, evaluates market conditions, and executes trades automatically based on SMA crossover signals and a stop-loss mechanism.

Dependencies/Requirements:
- Python 3.7+
- Alpaca Paper Trading Account and Keys:
	Sign up for an Alpaca paper trading account.
	Get your API Key and Secret from the Alpaca dashboard.
	Replace these placeholders in the script with your actual credentials:
		API_KEY = 'YOUR_API_KEY'
		SECRET_KEY = 'YOUR_SECRET_KEY'

- Required Python packages: pip install alpaca-py

Bot Description:
Strategy Summary
Buy: When the current price is below the 20-period SMA and no position is currently open.
Sell: When the current price is above the SMA and a position is open.
Stop-Loss: Sells if price drops more than 0.5% from the entry price.
Volatility Filter: Skips trading if volatility (max-min price over the SMA period) is less than $0.30.

Trade Control
Cooldown period of 5 minutes between trades to avoid overtrading.

Logging
Logs each price, trade, P&L, and final account summary upon termination. 

Note: The bot is currently set to trade 'APPL', but this can be changed to any other stock on the NASDAQ and NYSE exchanges.