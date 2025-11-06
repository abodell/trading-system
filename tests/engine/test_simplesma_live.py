import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import time
from datetime import datetime
from src.engine.trading_engine import TradingEngine
from src.strategies.simple_sma import SimpleSMA
from src.brokers.alpaca_broker import AlpacaBroker
from src.data.crypto_data_provider import CryptoDataProvider
from src.data.stock_data_provider import StockDataProvider
from src.portfolio.risk_config import RiskConfig
from src.portfolio.position_manager import PositionManager

CRYPTO_SYMBOLS = ["BTC/USD", "ETH/USD", "XRP/USD"]
STOCK_SYMBOLS = ["AAPL", "UNH", "TSLA"]

INTERVAL = 300

broker = AlpacaBroker()
crypto_data = CryptoDataProvider(api_key = broker.client.api_key, secret_key = broker.client.secret_key)
stock_data = StockDataProvider(api_key = broker.client.api_key, secret_key = broker.client.secret_key)

risk_config = RiskConfig(
    max_position_size=0.05,
    stop_loss_pct=0.05,
    take_profit_pct=0.10
)

engine = TradingEngine(
    broker=broker,
    data_provider_crypto=crypto_data,
    data_provider_stock=stock_data
)

for symbol in CRYPTO_SYMBOLS:
    strategy = SimpleSMA(broker, symbol, crypto_data, short_window = 5, long_window = 20)
    pos_mgr = PositionManager(risk_config=risk_config)
    engine.add_strategy(
        symbol=symbol,
        strategy=strategy,
        risk_config=risk_config,
        position_manager=pos_mgr,
        interval_seconds=INTERVAL,
        asset_type="crypto"
    )
    print(f"Registered crypto strategy for {symbol}...")

for symbol in STOCK_SYMBOLS:
    strategy = SimpleSMA(broker, symbol, stock_data, short_window = 5, long_window = 20)
    pos_mgr = PositionManager(risk_config)
    engine.add_strategy(
        symbol=symbol,
        strategy=strategy,
        risk_config=risk_config,
        position_manager=pos_mgr,
        interval_seconds=INTERVAL,
        asset_type="stock"
    )
    print(f"Registered stock strategy for {symbol}...")

print(f"[{datetime.now()}] Starting SimpleSMA live multi-symbol test...")
engine.start()

try:
    while True:
        time.sleep(600)
        engine.print_status()
except KeyboardInterrupt:
    print("\nGraceful shutdown requested. Stopping engine...")
    engine.stop()
