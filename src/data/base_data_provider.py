from abc import ABC, abstractmethod
from typing import Optional
import pandas as pd

class BaseDataProvider(ABC):
    """
    Abstract data provider for strategies. Implementations can be:
    - Real-time (REST polling or WebSocket) under Basic Market Data (IEX)
    - Historical bars for backtesting
    """

    @abstractmethod
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """ Return the latest traded price for symbol, or None if unavailable """
        pass

    @abstractmethod
    def get_bars(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> pd.DataFrame:
        """
        Return a DataFrame of OHLCV bars for the symbol
        timeframe examples: '1Min', '5Min', '15Min', '1Hour', '1Day'
        Implementations can map this to alpaca-py constructs
        """
        pass
    