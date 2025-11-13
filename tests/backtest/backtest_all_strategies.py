import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backtesting.backtest_engine import BacktestEngine
from src.strategies import simple_sma, rsi_strategy, macd_strategy, mean_reversion_strategy
from src.strategies.strategy_ensemble import StrategyEnsemble
from src.data.stock_data_provider import StockDataProvider
from src.data.crypto_data_provider import CryptoDataProvider
from src.brokers.alpaca_broker import AlpacaBroker
import pandas as pd

strategies = {
    "SimpleSMA": simple_sma.SimpleSMA,
    "RSI": rsi_strategy.RSIStrategy,
    "MACD": macd_strategy.MACDStrategy,
    "MeanReversion": mean_reversion_strategy.MeanReversionStrategy,
}

stocks = ["AAPL", "UNH", "TSLA"]
cryptos = ["BTC/USD", "ETH/USD", "XRP/USD"]

broker = AlpacaBroker()
stock_data = StockDataProvider(broker.client.api_key, broker.client.secret_key)
crypto_data = CryptoDataProvider(broker.client.api_key, broker.client.secret_key)
results = []

for name, cls in strategies.items():
    for symbol in stocks + cryptos:
        data_provider = crypto_data if "/" in symbol else stock_data

        strat = cls(broker, "AAPL", data_provider)
        engine = BacktestEngine(
            strategy = strat,
            broker = broker,
            data_provider = data_provider,
            starting_cash = 10000,
            slippage_pct = 0.0005,
            commission_crypto_pct = 0.0025,
            commission_stock_fixed = 0.0,
        )
        result = engine.run(symbol = symbol, days_back = 365)
        results.append(result.summary())

print("\n=== Running Strategy Ensemble across all symbols ===")
for symbol in stocks + cryptos:
    data_provider = crypto_data if "/" in symbol else stock_data

    sma = simple_sma.SimpleSMA(broker, symbol, data_provider)
    rsi = rsi_strategy.RSIStrategy(broker, symbol, data_provider)
    macd = macd_strategy.MACDStrategy(broker, symbol, data_provider)
    meanrev = mean_reversion_strategy.MeanReversionStrategy(broker, symbol, data_provider)

    ensemble = StrategyEnsemble(broker, symbol, [sma, rsi, macd, meanrev], verbose = True)

    engine = BacktestEngine(
        strategy = ensemble,
        broker=broker,
        data_provider=data_provider,
        starting_cash=10000,
        slippage_pct=0.0005,
        commission_crypto_pct=0.0025,
        commission_stock_fixed=0.0,
    )

    result = engine.run(symbol = symbol, days_back = 365)
    result.strategy_name = "Ensemble"
    results.append(result.summary())

pd.DataFrame(results).to_csv("results/strategy_comparison.csv", index = False)
print("Comparison file saved -> results/strategy_comparison.csv")