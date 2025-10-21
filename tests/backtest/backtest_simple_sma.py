import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backtesting.backtest_engine import BacktestEngine
from src.brokers.alpaca_broker import AlpacaBroker
from src.data.stock_data_provider import StockDataProvider
from src.strategies.simple_sma import SimpleSMA

def run_backtest(symbol: str, days_back: int = 60):
    """ Run a single backtest for a symbol """
    print(f"\n{'='*60}")
    print(f"Starting backtest for {symbol}")
    print(f"{'='*60}\n")

    # Setup
    broker = AlpacaBroker(paper = True)
    provider = StockDataProvider(
        api_key = broker.client.api_key,
        secret_key = broker.client.secret_key
    )
    strategy = SimpleSMA(broker, symbol, data_provider = provider)

    # Run backtest
    engine = BacktestEngine(strategy, broker, provider)
    result = engine.run(symbol, days_back = days_back)

    return result

def main():
    """ Run backtests on multiple symbols """
    symbols = [
        ("BMNR", 120),
        ("IREN", 120),
        ("VUG", 120)
    ]

    results = []

    for symbol, days_back in symbols:
        result = run_backtest(symbol, days_back = days_back)
        results.append(result)
    
    print(f"\n{'='*60}")
    print("OVERALL BACKTEST SUMMARY")
    print(f"{'='*60}\n")

    for result in results:
        print(
            f"{result['symbol']:6} | "
            f"Trades: {result['total_trades']:2} | "
            f"Return: {result['return_pct']:7.2f}% | "
            f"Win Rate: {result['win_rate']*100:5.1f}%"
        )

if __name__ == "__main__":
    main()