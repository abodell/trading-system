from datetime import datetime, timedelta, timezone
from typing import Optional
import pandas as pd
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.strategies.base_strategy import BaseStrategy
from src.brokers.base_broker import BaseBroker
from src.data.base_data_provider import BaseDataProvider

class BacktestEngine:
    """
    Backtesting engine that replays historical data and executes strategies.
    """

    def __init__(
            self,
            strategy: BaseStrategy,
            broker: BaseBroker,
            data_provider: BaseDataProvider,
            starting_cash: float = 100000.0
    ):
        self.strategy = strategy
        self.broker = broker
        self.data_provider = data_provider
        self.starting_cash = starting_cash
        self.current_cash = starting_cash

        # Tracking
        self.trades = []
        self.equity_curve = []
        self.position = None # Track open position: {"entry_price", "entry_date", "qty"}
    
    def run(
            self,
            symbol: str,
            days_back: int = 60,
            timeframe: str = "1Day",
    ) -> dict:
        """
        Run backtest on historical data.

        Args:
            symbol: Trading symbol (e.g., "AAPL")
            days_back: How many days of history to backtest
            timeframe: Bar timeframe ("1Min", "1Hour", "1Day", etc)
        
        Returns:
            Dictionary with backtest results
        """
        print(f"Starting backtest: {symbol} ({days_back} days back)")

        # Fetch historical data
        bars = self.data_provider.get_bars(
            symbol, timeframe, limit = 1000, days_back = days_back
        )

        if bars.empty:
            print(f"No data available for {symbol}")
            return {}
        
        print(f"Fetched {len(bars)} bars")

        # Process each bar
        for idx, (timestamp, bar) in enumerate(bars.iterrows()):
            # Pass bars up to this point to strategy
            bars_so_far = bars.iloc[:idx+1].copy()
            signal = self.strategy.evaluate_signal(bars=bars_so_far)
            
            close_price = bar["close"]
            print(f"[{idx}] {timestamp} | Close: ${close_price:.2f} | Signal: {signal}")

            # Execute trades
            if signal == "buy" and self.position is None:
                self.position = {
                    "entry_price": close_price,
                    "entry_date": timestamp,
                    "qty": 1
                }
                print(f"-> ENTER LONG @ ${close_price:.2f}")
            
            elif signal == "sell" and self.position is not None:
                pnl = (close_price - self.position['entry_price']) * self.position['qty']
                self.trades.append({
                    "entry_date": self.position['entry_date'],
                    "entry_price": self.position['entry_price'],
                    "exit_date": timestamp,
                    "exit_price": close_price,
                    "pnl": pnl
                })
                print(f"-> EXIT LONG @ ${close_price:.2f} | P&L: {pnl:.2f}")
                self.position = None

        return {
            "symbol": symbol,
            "bars_processed": len(bars),
            "status": "complete"
        }

if __name__ == "__main__":
    from src.brokers.alpaca_broker import AlpacaBroker
    from src.data.stock_data_provider import StockDataProvider
    from src.strategies.simple_sma import SimpleSMA
    
    broker = AlpacaBroker(paper=True)
    provider = StockDataProvider(
        api_key=broker.client.api_key,
        secret_key=broker.client.secret_key,
    )
    strategy = SimpleSMA(broker, "BMNR", data_provider=provider)
    
    engine = BacktestEngine(strategy, broker, provider)
    results = engine.run("BMNR", days_back=120)
    print(results)