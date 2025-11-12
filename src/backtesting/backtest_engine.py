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
            slippage_pct: float = 0.0005,
            commission_stock_fixed: float = 0, # Alpaca does not charge fees on Stock trades
            commission_crypto_pct: float = 0.0025,
    ):
        self.strategy = strategy
        self.broker = broker
        self.data_provider = data_provider
        self.starting_cash = starting_cash
        self.current_cash = starting_cash
        self.verbose = verbose
        self.slippage_pct = slippage_pct
        self.commission_stock_fixed = commission_stock_fixed
        self.commission_crypto_pct = commission_crypto_pct

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
                # Apply slippage
                slip_price = price * (1 + self.slippage_pct)
                # Commission
                notional = qty * slip_price
                if "USD" in symbol or "/" in symbol:
                    commission = notional * self.commission_crypto_pct
                else:
                    commission = self.commission_stock_fixed
                
                total_cost = notional + commission
                if total_cost > cash:
                    qty *= cash / total_cost
                    notional = qty * slip_price
                    total_cost = notional + commission
                
                cash -= total_cost
                position_qty = qty
                self.entry_price = slip_price
                self.entry_time = bars.index[i]
                if self.verbose:
                    print(f"[BUY] {symbol} x{qty:.3f} @ {price:.4f}")
            
            elif signal == "sell" and position_qty > 0:
                slip_price = price * (1 - self.slippage_pct)
                notional = position_qty * slip_price

                if "USD" in symbol or "/" in symbol:
                    commission = notional * self.commission_crypto_pct
                else:
                    commission = self.commission_stock_fixed
                
                cash += notional - commission
                pnl = (slip_price - self.entry_price) * position_qty - commission
                trades.append(
                    {
                        "symbol": symbol,
                        "entry_price": self.entry_price,
                        "exit_price": slip_price,
                        "qty": position_qty,
                        "pnl": pnl,
                        "entry_time": self.entry_time,
                        "exit_time": bars.index[i],
                        "commission": commission,
                        "slippage": self.slippage_pct
                    }
                )

                position_qty = 0
                self.entry_price = None
                self.entry_time = None

            total_equity = cash + position_qty * price
            equity_curve.append({"equity": total_equity})

        if position_qty > 0 and self.entry_price is not None:
            final_price = bars['close'].iloc[-1]
            # Apply slippage
            exit_price = final_price * (1 - self.slippage_pct)
            # Notional
            notional = position_qty * exit_price
            if "USD" in symbol or "/" in symbol:
                commission = notional * self.commission_crypto_pct
            else:
                commission = self.commission_stock_fixed

            cash += notional - commission
            pnl = (exit_price - self.entry_price) * position_qty - commission
            trades.append(
                {
                    "symbol": symbol,
                    "entry_price": self.entry_price,
                    "exit_price": final_price,
                    "qty": position_qty,
                    "pnl": pnl,
                    "entry_time": self.entry_time,
                    "exit_time": bars.index[-1],
                    "commission": commission,
                    "slippage": self.slippage_pct
                }
            )
            if self.verbose:
                print(f"[FINAL CLOSE] {symbol} @ {exit_price:.4f} | P&L = {pnl:.4f}")
        
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