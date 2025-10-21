class RiskConfig:
    """ Risk parameters for positions sizing and trade management. """

    def __init__(
            self,
            risk_per_trade: float = 0.02, # 2% of account per trade,
            stop_loss_pct: float = 0.05, # 5% stop loss
            take_profit_pct: float = 0.10, # 10% take profit
            max_position_size: int = 100, # Max qty per trade
            max_positions_open: int = 3, # Max concurrent positions
            max_daily_loss_pct: float = 0.05, # Max 5% loss per day
    ):
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_position_size = max_position_size
        self.max_positions_open = max_positions_open
        self.max_daily_loss_pct = max_daily_loss_pct
    
    def __repr__(self):
        return (
            f"RiskConfig("
            f"risk={self.risk_per_trade*100:.1f}%, "
            f"stop_loss={self.stop_loss_pct*100:.1f}%, "
            f"take_profit={self.take_profit_pct*100:.1f}%)"
        )