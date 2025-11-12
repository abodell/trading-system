from typing import Optional
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.strategies.base_strategy import BaseStrategy
from src.portfolio.position_manager import PositionManager
from src.portfolio.risk_config import RiskConfig
from src.brokers.base_broker import BaseBroker
from src.data.base_data_provider import BaseDataProvider
from src.backtesting.backtest_result import BacktestResult

class BacktestEngine:
    """
    Simplified, standardized backtesting engine.
    Can run any BaseStrategy subclass over historical bars
    """

    def __init__(
            self,
            strategy: BaseStrategy,
            broker: BaseBroker,
            data_provider: BaseDataProvider,
            starting_cash: float = 10_000.0,
            risk_config: Optional[RiskConfig] = None,
            verbose: bool = False,
    ):
        self.strategy = strategy
        self.broker = broker
        self.data_provider = data_provider
        self.starting_cash = starting_cash
        self.current_cash = starting_cash
        self.verbose = verbose

        self.position_manager = PositionManager(risk_config or RiskConfig())

        self.trades = []
        self.equity_curve = []
        self.position = 0.0
        self.entry_price = None
        self.entry_time = None
    
    def run(
            self,
            symbol: str,
            days_back: int = 365,
            timeframe: str = "1Day",
            limit: int = 1000,
    ) -> BacktestResult:
        """ Run a full backtest for a given symbol. """
        print(f"\n=== Backtest Start: {symbol} | {days_back} days @ {timeframe} ===")
        
        bars = self.data_provider.get_bars(
            symbol = symbol, timeframe = timeframe, limit = limit, days_back = days_back
        )
        if bars is None or bars.empty:
            print("No historical bars found.")
            return BacktestResult(symbol, self.starting_cash, [], 0, [])
    
        bars = bars.sort_index()
        cash = self.starting_cash
        position_qty = 0.0
        trades = []
        equity_curve = []

        for i in range(20, len(bars)):
            window = bars.iloc[: i + 1].copy()
            signal = self.strategy.evaluate_signal(window)
            price = window["close"].iloc[-1]

            if signal == "buy" and position_qty == 0:
                qty = (cash * self.position_manager.config.risk_per_trade) / price
                cash -= qty * price
                position_qty = qty
                self.entry_price = price
                self.entry_time = bars.index[i]
                if self.verbose:
                    print(f"[BUY] {symbol} x{qty:.3f} @ {price:.4f}")
            
            elif signal == "sell" and position_qty > 0:
                cash += position_qty * price
                pnl = (price - self.entry_price) * position_qty
                trades.append(
                    {
                        "symbol": symbol,
                        "entry_price": self.entry_price,
                        "exit_price": price,
                        "qty": position_qty,
                        "pnl": pnl,
                        "entry_time": self.entry_time,
                        "exit_time": bars.index[i]
                    }
                )
                if self.verbose:
                    print(f"[SELL] {symbol} | P&L = {pnl:.4f}")
                position_qty = 0
                self.entry_price = None
                self.entry_time = None
            
            total_equity = cash + position_qty * price
            equity_curve.append({"equity": total_equity})

        if position_qty > 0 and self.entry_price is not None:
            final_price = bars['close'].iloc[-1]
            cash += position_qty * final_price
            pnl = (final_price - self.entry_price) * position_qty
            trades.append(
                {
                    "symbol": symbol,
                    "entry_price": self.entry_price,
                    "exit_price": final_price,
                    "qty": position_qty,
                    "pnl": pnl,
                    "entry_time": self.entry_time,
                    "exit_time": bars.index[-1]
                }
            )
            if self.verbose:
                print(f"[FINAL CLOSE] {symbol} @ {final_price:.4f} | P&L = {pnl:.4f}")
        
        result = BacktestResult(
            symbol = symbol,
            starting_cash = self.starting_cash,
            trades = trades,
            bars_processed = len(bars),
            equity_curve = equity_curve,
        )

        print(f"\n--- Backtest Complete ---")
        result.print_summary()
        return result