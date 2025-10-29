from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime
from src.strategies.base_strategy import BaseStrategy
from src.portfolio.risk_config import RiskConfig
from src.portfolio.position_manager import PositionManager

@dataclass
class StrategyConfig:
    """ Configuration for a single strategy / symbol pair """
    symbol: str
    strategy: BaseStrategy
    risk_config: RiskConfig
    position_manager: PositionManager
    interval_seconds: int
    asset_type: str = "stock"
    enabled: bool = True
    last_run: Optional[datetime] = None
    trades_this_session: int = field(default = 0)
    pnl_this_session: float = field(default = 0.0)

    def __repr__(self) -> str:
        return(
            f"StrategyConfig({self.symbol}, "
            f"interval={self.interval_seconds}s, "
            f"asset_type={self.asset_type})"
        )
