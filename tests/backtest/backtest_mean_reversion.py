import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.mean_reversion_strategy import MeanReversionStrategy
from src.brokers.alpaca_broker import AlpacaBroker
from src.data.stock_data_provider import StockDataProvider

broker = AlpacaBroker()
data = StockDataProvider(broker.client.api_key, broker.client.secret_key)
strategy = MeanReversionStrategy(broker, "AAPL", data, lookback = 20, threshold = 1.5)

engine = BacktestEngine(strategy, broker, data)
result = engine.run("AAPL", days_back = 365)
result.to_csv(f"results/backtests/MEAN_REVERSION_AAPL_{datetime.now().date()}.csv")
result.plot_equity()