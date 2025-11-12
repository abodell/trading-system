from typing import List, Dict
import pandas as pd
import os
import matplotlib.pyplot as plt

class BacktestResult:
    """ Stores and calculates backtest results and metrics """

    def __init__(
            self,
            symbol: str,
            starting_cash: float,
            trades: List[Dict],
            bars_processed: int,
            equity_curve: List[Dict]
    ):
        self.symbol = symbol
        self.starting_cash = starting_cash
        self.trades = trades
        self.bars_processed = bars_processed
        self.equity_curve = equity_curve
    
    @property
    def total_trades(self) -> int:
        return len(self.trades)
    
    @property
    def total_pnl(self) -> float:
        return sum(t["pnl"] for t in self.trades) if self.trades else 0.0
    
    @property
    def total_commission(self) -> float:
        """ Sum of all commission entries """
        return sum(t.get("commission", 0.0) for t in self.trades)
    
    @property
    def win_rate(self) -> float:
        if not self.trades:
            return 0.0
        wins = len([t for t in self.trades if t['pnl'] > 0])
        return wins / len(self.trades)
    
    @property
    def num_wins(self) -> int:
        return len([t for t in self.trades if t['pnl'] > 0])
    
    @property
    def num_losses(self) -> int:
        return len([t for t in self.trades if t['pnl'] < 0])
    
    @property
    def avg_win(self) -> float:
        wins = [t['pnl'] for t in self.trades if t['pnl'] > 0]
        return sum(wins) / len(wins) if wins else 0.0
    
    @property
    def avg_loss(self) -> float:
        losses = [t['pnl'] for t in self.trades if t['pnl'] < 0]
        return sum(losses) / len(losses) if losses else 0.0
    
    @property
    def return_pct(self) -> float:
        """ Return as percentage of starting capital """
        return (self.total_pnl / self.starting_cash) * 100
    
    @property
    def max_drawdown(self) -> float:
        """
        Calculate maximum drawdown as percentage.
        Drawdown = (Peak - Trough) / Peak
        """
        if not self.equity_curve:
            return 0.0
        
        equity_values = [e["equity"] for e in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0.0

        for equity in equity_values:
            if equity > peak:
                peak = equity
            drawdown = (peak - equity) / peak
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def summary(self) -> Dict:
        """ Return all metrics as a dictionary """
        return {
            "symbol": self.symbol,
            "bars_processed": self.bars_processed,
            "total_trades": self.total_trades,
            "total_pnl": self.total_pnl,
            "return_pct": self.return_pct,
            "win_rate": self.win_rate,
            "num_wins": self.num_wins,
            "num_losses": self.num_losses,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "max_drawdown": self.max_drawdown,
            "total_commission": self.total_commission,
        }
    
    def print_summary(self):
        """Pretty print the summary."""
        s = self.summary()
        print("\n" + "="*60)
        print(f"BACKTEST RESULTS: {s['symbol']}")
        print("="*60)
        print(f"Bars Processed: {s['bars_processed']}")
        print(f"Total Trades: {s['total_trades']}")
        print(f"Total P&L: ${s['total_pnl']:.2f}")
        print(f"Commissions Paid: ${s['total_commission']:.2f}")
        print(f"Return: {s['return_pct']:.2f}%")
        print(f"Max Drawdown: {s['max_drawdown']*100:.2f}%")
        print(f"Win Rate: {s['win_rate']*100:.1f}% ({s['num_wins']}/{s['total_trades']})")
        print(f"Avg Win: ${s['avg_win']:.2f} | Avg Loss: ${s['avg_loss']:.2f}")
        print("="*60 + "\n")
    
    def plot_equity(self, save_path: str = None):
        """ Quick matplotlib plot for equity curve """
        if not self.equity_curve:
            print("No equity data to plot.")
            return
        
        eq = [e["equity"] for e in self.equity_curve]
        plt.figure(figsize=(10, 4))
        plt.plot(eq, label=f"{self.symbol} Equity", color="tab:blue")
        plt.title(f"Equity Curve - {self.symbol}")
        plt.xlabel("Bars")
        plt.ylabel("Equity ($)")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"Saved equity curve to {save_path}")
        else:
            plt.show()
    
    def to_csv(self, path: str):
        """ Save equity curve and trade summary to CSV. """
        os.makedirs(os.path.dirname(path), exist_ok = True)
        eq_df = pd.DataFrame(self.equity_curve)
        eq_df.to_csv(path, index=False)
        print(F"Equity curve data saved -> {path}")

        summ_path = path.replace(".csv", "_summary.csv")
        pd.DataFrame([self.summary()]).to_csv(summ_path, index = False)
        print(f"Summary metrics saved -> {summ_path}")