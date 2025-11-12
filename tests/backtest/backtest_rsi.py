import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies.rsi_strategy import RSIStrategy
from src.brokers.alpaca_broker import AlpacaBroker
from src.data.stock_data_provider import StockDataProvider
from datetime import datetime

broker = AlpacaBroker()
data = StockDataProvider(broker.client.api_key, broker.client.secret_key)
strategy = RSIStrategy(broker, "AAPL", data)

engine = BacktestEngine(strategy, broker, data)
result = engine.run("AAPL", days_back=365)
result.to_csv(f"results/backtests/RSI_AAPL_{datetime.now().date()}.csv")
result.plot_equity()