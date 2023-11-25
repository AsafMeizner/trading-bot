# variables.py
symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'FB', 'NFLX', 'TSLA', 'NVDA', 'AMD', 'INTC']

# Current best parameters
best_parameters = {
    "short_window": 40,
    "long_window": 100,
    "rsi_period": 14,
    "overbought_threshold": 70,
    "oversold_threshold": 30,
    "risk_percent": 0.02,
    "stake_per_trade": 0.02,
}

# Perform a grid search for parameter optimization
short_window_values = list(range(20, 61, 5))  # Range from 20 to 60 with step size 5
long_window_values = list(range(50, 151, 10))  # Range from 50 to 150 with step size 10
rsi_period_values = list(range(10, 21, 2))  # Range from 10 to 20 with step size 2
overbought_threshold_values = list(range(60, 81, 5))  # Range from 60 to 80 with step size 5
oversold_threshold_values = list(range(20, 41, 5))  # Range from 20 to 40 with step size 5
risk_percent_values = [0.01, 0.015, 0.02, 0.025, 0.03]  # Specific values to check
stake_per_trade_values = [0.01, 0.015, 0.02, 0.025, 0.03]  # Specific values to check