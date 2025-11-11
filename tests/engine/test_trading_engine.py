import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import time
from datetime import datetime
from src.brokers.alpaca_broker import AlpacaBroker
from src.data.stock_data_provider import StockDataProvider
from src.data.crypto_data_provider import CryptoDataProvider
from src.strategies.simple_sma import SimpleSMA
from src.strategies.test_strategy import TestStrategy
from src.portfolio.risk_config import RiskConfig
from src.portfolio.position_manager import PositionManager
from src.engine import TradingEngine

def test_engine_stock_and_crypto():
    """ Test engine with one stock strategy and one crypto strategy """
    broker = AlpacaBroker()
    stock_data = StockDataProvider(broker.client.api_key, broker.client.secret_key)
    crypto_data = CryptoDataProvider(broker.client.api_key, broker.client.secret_key)

    engine = TradingEngine(
        broker = broker,
        data_provider_stock = stock_data,
        data_provider_crypto = crypto_data,
        log_dir = "logs"
    )

    # Strategy 1: Stock (AAPL)
    risk_config_1 = RiskConfig(
        risk_per_trade = 0.02,
        stop_loss_pct = 0.05,
        take_profit_pct = 0.10,
        max_position_size = 10
    )
    position_mgr_1 = PositionManager(risk_config_1)
    strategy_1 = SimpleSMA(
        symbol = "AAPL",
        broker = broker,
        data_provider = stock_data,
        short_window = 5,
        long_window = 20
    )
    engine.add_strategy(
        symbol = "AAPL",
        strategy = strategy_1,
        risk_config = risk_config_1,
        position_manager = position_mgr_1,
        interval_seconds = 300,
        asset_type = "stock"
    )

    risk_config_2 = RiskConfig(
        risk_per_trade = 0.02,
        stop_loss_pct = 0.05,
        take_profit_pct = 0.10,
        max_position_size = 0.1
    )
    position_mgr_2 = PositionManager(risk_config_2)
    strategy_2 = SimpleSMA(
        symbol = "XRP/USD",
        broker = broker,
        data_provider = crypto_data,
        short_window = 5,
        long_window = 20
    )
    engine.add_strategy(
        symbol = "XRP/USD",
        strategy = strategy_2,
        risk_config = risk_config_2,
        position_manager = position_mgr_2,
        interval_seconds = 300,
        asset_type = "crypto"
    )

    engine.start()

    print("Engine running... Press CTRL + C to stop")
    try:
        for i in range(300):
            time.sleep(1)
            if i % 30 == 0:
                engine.print_status()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        engine.stop()
        engine.print_status()

def test_engine_with_test_strategy():
    """ Validate engine pipeline with predicatable signals """
    broker = AlpacaBroker()
    stock_data = StockDataProvider(broker.client.api_key, broker.client.secret_key)
    crypto_data = CryptoDataProvider(broker.client.api_key, broker.client.secret_key)

    engine = TradingEngine(
        broker = broker, 
        data_provider_stock = stock_data,
        data_provider_crypto = crypto_data,
        log_dir = "logs"
    )

    # Test with XRP/USD only (faster feedback)
    risk_config = RiskConfig(
        risk_per_trade=0.02,
        stop_loss_pct=0.05,
        take_profit_pct=0.10,
        max_position_size=5
    )
    position_mgr = PositionManager(risk_config)
    
    strategy = TestStrategy(
        broker=broker,
        symbol="ETH/USD",
        data_provider=crypto_data
    )
    
    engine.add_strategy(
        symbol="ETH/USD",
        strategy=strategy,
        risk_config=risk_config,
        position_manager=position_mgr,
        interval_seconds=10,  # Check every 10 seconds
        asset_type="crypto"
    )

    engine.start()

    print("Engine running with TestStrategy... Press CTRL + C to stop")
    try:
        for i in range(120):  # Run for 2 minutes
            time.sleep(1)
            if i % 30 == 0:
                engine.print_status()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        engine.stop()
        engine.print_status()

if __name__ == "__main__":
    test_engine_with_test_strategy()