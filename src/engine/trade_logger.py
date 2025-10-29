import csv
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

class TradeLogger:
    """ Logs all trades to CSV and generates daily summaries """

    def __init__(self, log_dir: str = "logs"):
        """
        Initialize trade logger.

        Args:
            log_dir: Directory to store trade logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok = True)
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbole for use in filenames.
        
        Removes "/" from crypto currencies to avoid path issues
        """
        return symbol.replace("/", "")
    
    def log_trade(
            self,
            symbol: str,
            entry_price: float,
            exit_price: float,
            quantity: int,
            entry_time: datetime,
            exit_time: datetime,
            exit_reason: str,
            pnl: float,
            pnl_percent: float
    ) -> None:
        """
        Log a completed trade to CSV.

        Args:
            symbol: Trading symbol
            entry_price: Entry price per share
            exit_price: Exit price per share
            quantity: Number of shares
            entry_time: Entry timestamp
            exit_time: Exit timestamp
            exit_reason: Why trade closed ("signal", "stop_loss", "take_profit")
            pnl: Profit/loss in dollars
            pnl_percent: Return percentage
        """
        today = datetime.now().strftime("%Y-%m-%d")
        normalized_symbol = self._normalize_symbol(symbol)
        log_file = self.log_dir / f"trades_{normalized_symbol}_{today}.csv"

        file_exists = log_file.exists()

        with open(log_file, "a", newline="") as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow([
                    "symbol",
                    "entry_time",
                    "exit_time",
                    "entry_price",
                    "exit_price",
                    "quantity",
                    "pnl",
                    "pnl_percent",
                    "exit_reason"
                ])
            
            writer.writerow([
                symbol,
                entry_time.isoformat(),
                exit_time.isoformat(),
                f"{entry_price:.8f}",
                f"{exit_price:.8f}",
                f"{quantity:.8f}",
                f"{pnl:.4f}",
                f"{pnl_percent:.2f}%",
                exit_reason
            ])
        
    def log_daily_summary(
            self,
            summary_data: dict
    ) -> None:
        """
        Log daily performance summary as JSON

        Args:
            summary_dat: Dict with daily metrics
        """
        today = datetime.now().strftime("%Y-%m-%d")
        summary_file = self.log_dir / f"daily_summary_{today}.json"

        with open(summary_file, "w") as f:
            json.dump(summary_data, f, indent = 2, default = str)
    
    def get_today_trades(self, symbol: str) -> list:
        """
        Get all trades logged today for a symbol.

        Args:
            symbol: Trading symbol
        
        Returns:
            List of trade dicts
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"trades_{symbol}_{today}.csv"

        if not log_file.exists():
            return []
        
        trades = []
        with open(log_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                trades.append(row)
        
        return trades