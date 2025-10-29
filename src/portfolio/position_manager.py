from typing import Optional
import pandas as pd
from .risk_config import RiskConfig
from datetime import datetime


class PositionManager:
    """Manages position sizing and tracking based on risk parameters"""

    def __init__(self, risk_config: RiskConfig):
        self.config = risk_config
        self.open_positions = []
        self.daily_pnl = 0.0  # Track daily P&L
    
    def calculate_position_size(
            self,
            account_equity: float,
            entry_price: float,
    ) -> int:
        """
        Calculate position size based on risk.

        Formula: position_size = (account_equity * risk_per_trade) / 
                 (entry_price * stop_loss_pct)

        Args:
            account_equity: Current account equity
            entry_price: Entry price per share
        
        Returns:
            Position size (number of shares), capped at max_position_size
        """
        # Calculate stop loss distance in dollars
        stop_loss_distance = entry_price * self.config.stop_loss_pct
        
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
        """Record a new open position."""
        if entry_date is None:
            entry_date = datetime.now()
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
    
    def can_open_position(self, account_equity: float) -> bool:
        """
        Check if we can open a new position based on limits.

        Returns False if:
            - Already at max open positions
            - Would exceed max daily loss limit

        Args:
            account_equity: Current account equity
        
        Returns:
            bool: True if position can be opened
        """
        # Check number of open positions
        if self.get_num_open_positions() >= self.config.max_positions_open:
            return False
        
        # Check max daily loss (uses self.daily_pnl)
        max_daily_loss = -(account_equity * self.config.max_daily_loss_pct)
        if self.daily_pnl < max_daily_loss:
            return False
        
        return True
    
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
    
    def close_position(
            self,
            symbol: str,
            exit_price: float
    ) -> None:
        """
        Close a position and update daily P&L.
        
        Args:
            symbol: Symbol to close
            exit_price: Exit price per share
        """
        for pos in self.open_positions:
            if pos["symbol"] == symbol:
                pnl = (exit_price - pos["entry_price"]) * pos["qty"]
                self.daily_pnl += pnl
                break
        
        self.open_positions = [
            p for p in self.open_positions if p["symbol"] != symbol
        ]

    def get_num_open_positions(self) -> int:
        """Get count of open positions"""
        return len(self.open_positions)
    
    def reset_daily_pnl(self) -> None:
        """Reset daily P&L (call at end of day)"""
        self.daily_pnl = 0.0