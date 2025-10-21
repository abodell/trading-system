import math
from typing import Optional
import pandas as pd
from .risk_config import RiskConfig

class PositionManager:
    """ Manages position sizing based on risk parameters """

    def __init__(self, risk_config: RiskConfig):
        self.config = risk_config
        self.open_positions = []
    
    def calculate_position_size(
            self,
            account_equity: float,
            stop_loss_distance: float,
    ) -> int:
        """
        Calculate position size based on risk

        Formula: position_size = (account_equity * risk_per_trade) / stop_loss_distance

        Args:
            account_equity: Current account equity
            stop_loss_distance: Distance from entry to stop loss (in dollars)
        
        Returns:
            Position size (number of shares), capped at max_position_size
        """
        if stop_loss_distance <= 0:
            return 0
        
        # Calculate how many shares we can buy with risk formula
        risk_amount = account_equity * self.config.risk_per_trade
        position_size = risk_amount / stop_loss_distance

        # Cap at max position size
        position_size = min(int(position_size), self.config.max_position_size)

        return position_size
    
    def open_position(
            self,
            symbol: str,
            entry_price: float,
            qty: int,
            entry_date: Optional[pd.Timestamp] = None
    ):
        """ Record a new open position. """
        stop_loss_price = entry_price * (1 - self.config.stop_loss_pct)
        take_profit_price = entry_price * (1 + self.config.take_profit_pct)

        position = {
            "symbol": symbol,
            "entry_price": entry_price,
            "entry_date": entry_date,
            "qty": qty,
            "stop_loss_price": stop_loss_price,
            "take_profit_price": take_profit_price
        }
        self.open_positions.append(position)
        return position
    
    def check_position_exit(self, symbol: str, current_price: float):
        """
        Check if position should exit due to stop loss or take profit.

        Returns: "stop_loss", "take_profit", or None
        """
        for pos in self.open_positions:
            if pos["symbol"] == symbol:
                if current_price <= pos["stop_loss_price"]:
                    return "stop_loss"
                if current_price >= pos["take_profit_price"]:
                    return "take_profit"
        return None
    
    def close_position(self, symbol: str) -> None:
        """ Remove a closed position from tracking """
        self.open_positions = [p for p in self.open_positions if p["symbol"] != symbol]

    def get_num_open_positions(self) -> int:
        """ Get count of open positions """
        return len(self.open_positions)