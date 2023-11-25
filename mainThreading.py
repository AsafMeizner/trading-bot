# trading_bot.py
import yfinance as yf
import backtrader as bt
from itertools import product
import threading
from variables import *
import queue
import time

class MyStrategy(bt.Strategy):
    params = best_parameters  # Use the best_parameters directly as default values

    def __init__(self):
        self.assets = self.datas  # List of data feeds for different assets

        for asset in self.assets:
            # Exponential Moving Averages for short and long windows
            asset.short_mavg = bt.indicators.SimpleMovingAverage(
                asset.close,
                period=self.params.short_window,
                plotname=f"{asset._name}_short_mavg"
            )
            asset.long_mavg = bt.indicators.SimpleMovingAverage(
                asset.close,
                period=self.params.long_window,
                plotname=f"{asset._name}_long_mavg"
            )

            # Relative Strength Index (RSI) for trend strength
            asset.rsi = bt.indicators.RelativeStrengthIndex(
                period=self.params.rsi_period,
                plotname=f"{asset._name}_rsi"
            )

            # Average True Range (ATR) for volatility-based position sizing
            asset.atr = bt.indicators.ATR(asset, period=14)

    def next(self):
        for i, asset in enumerate(self.assets):
            # Check if there is enough data
            if len(asset) > max(self.params.short_window, self.params.long_window, self.params.rsi_period):
                # Check if we already have an open position
                if self.getposition(data=asset).size == 0:
                    # Buy when short-term average crosses above long-term average and RSI is below oversold threshold
                    if (
                        asset.short_mavg > asset.long_mavg
                        and asset.rsi < self.params.oversold_threshold
                    ):
                        # Calculate position size based on risk percentage and stop loss
                        risk_amount = self.broker.getvalue() * self.params.risk_percent
                        atr_value = asset.atr[0]
                        stop_loss = asset.close[0] - atr_value * 1.5  # Adjust stop loss based on volatility
                        stake_size = risk_amount / (asset.close[0] - stop_loss)

                        # Execute buy order with a trailing stop
                        self.buy(data=asset, size=stake_size, exectype=bt.Order.StopTrail, trailamount=atr_value)

                # Sell when short-term average crosses below long-term average and RSI is above overbought threshold
                elif (
                    asset.short_mavg < asset.long_mavg
                    and asset.rsi > self.params.overbought_threshold
                ):
                    # Execute sell order
                    self.sell(data=asset)

def download_data_threaded(symbol, data_queue):
    try:
        # Download historical data
        data = yf.download(symbol, start='2022-01-01', end='2023-01-01')

        if len(data) == 0:
            print(f"Failed to download data for {symbol}: No data available")
            return

        # Add historical data to the queue
        data_queue.put((symbol, data))
    except Exception as e:
        print(f"Failed to download data for {symbol}: {e}") 

def run_backtest(strategy_params):
    cerebro = bt.Cerebro()
    cerebro.addstrategy(MyStrategy, **strategy_params)

    # Create a queue to store data from the threads
    data_queue = queue.Queue()

    # Create a list to store thread objects
    threads = []

    # Start a thread for each symbol
    for symbol in symbols:
        # Create a thread for downloading data
        thread = threading.Thread(target=download_data_threaded, args=(symbol, data_queue))
        threads.append(thread)

        # Start the thread
        thread.start()

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Process the data from the queue
    while not data_queue.empty():
        symbol, data = data_queue.get()

        # Add historical data to backtrader for each symbol
        data_feed = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(data_feed, name=symbol)

    if not cerebro.datas:
        print("No data available for backtesting. Exiting.")
        return None  # Return None in case of failure

    # Set initial capital and position sizing
    cerebro.broker.set_cash(100000)  # Set initial capital
    cerebro.addsizer(bt.sizers.PercentSizer, percents=strategy_params["stake_per_trade"] * 100)  # Dynamic position sizing
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # Minimum stake size

    print(f"Running backtest with parameters: {strategy_params}")

    try:
        cerebro.run()
        # Print the ending portfolio value
        ending_portfolio_value = cerebro.broker.getvalue()
        print(f"Ending Portfolio Value: {ending_portfolio_value}")
        return ending_portfolio_value
    except Exception as e:
        print(f"Backtest failed: {e}")
        return None  # Return None in case of failure

def test_best_parameters():
    best_portfolio_value = float("-inf")
    best_parameters_final = best_parameters.copy()

    # Create a grid of all possible combinations of parameter values
    parameter_combinations = list(product(
        short_window_values,
        long_window_values,
        rsi_period_values,
        overbought_threshold_values,
        oversold_threshold_values,
        risk_percent_values,
        stake_per_trade_values
    ))

    for params in parameter_combinations:
        # Use the current combination of parameters
        current_params = {
            "short_window": params[0],
            "long_window": params[1],
            "rsi_period": params[2],
            "overbought_threshold": params[3],
            "oversold_threshold": params[4],
            "risk_percent": params[5],
            "stake_per_trade": params[6],
        }

        # Run backtest with the current combination of parameters
        ending_portfolio_value = run_backtest(current_params)

        # Check if the backtest was successful and ending_portfolio_value is not None
        if ending_portfolio_value is not None:
            # Update best parameters if the current combination performs better
            if ending_portfolio_value > best_portfolio_value:
                best_portfolio_value = ending_portfolio_value
                best_parameters_final = current_params

    # Print the best parameters at the end
    print("\nBest Parameters:")
    print(best_parameters_final)
    print("Best Portfolio Value:", best_portfolio_value)

def run_strategy_with_yfinance():
    for symbol in symbols:
        data = yf.download(symbol, start='2022-01-01', end='2023-01-01')
        data = data[['Open', 'High', 'Low', 'Close', 'Volume']]

        cerebro = bt.Cerebro()
        cerebro.addstrategy(MyStrategy, **best_parameters)

        # Add historical data to backtrader
        data_feed = bt.feeds.PandasData(dataname=data)
        cerebro.adddata(data_feed)

        # Set initial capital and position sizing
        cerebro.broker.set_cash(100000)  # Set initial capital
        cerebro.addsizer(bt.sizers.PercentSizer, percents=best_parameters["stake_per_trade"] * 100)  # Dynamic position sizing
        cerebro.addsizer(bt.sizers.FixedSize, stake=10)  # Minimum stake size

        print(f"Running strategy with yfinance for {symbol} with parameters: {best_parameters}")
        cerebro.run()

        # Print the ending portfolio value
        ending_portfolio_value = cerebro.broker.getvalue()
        print(f"Ending Portfolio Value for {symbol}: {ending_portfolio_value}")

# Uncomment the function you want to run
# run_backtest(best_parameters)
test_best_parameters()
# run_strategy_with_yfinance()
