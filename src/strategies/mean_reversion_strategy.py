from src.strategies.base_strategy import BaseStrategy
from src.data.base_data_provider import BaseDataProvider
import pandas as pd
import numpy as np

class MeanReversionStrategy(BaseStrategy):
    """
    Simple mean reversion strategy using deviation from moving average.

    Buy when price < SMA - (threshold * stddev)
    Sell when price > SMA + (threshold * stddev)
    """

    def __init__(
            self,
            broker,
            symbol: str,
            data_provider: BaseDataProvider,
            lookback: int = 20,
            threshold: float = 1.5,
    ):
        super().__init__(broker, symbol)
        self.data_provider = data_provider
        self.lookback = lookback
        self.threshold = threshold

    def _get_recent_data(self, bars_back: int = None) -> pd.DataFrame:
        limit = max(self.lookback + 5, 40) if bars_back is None else bars_back
        return self.data_provider.get_bars(self.symbol, "1Day", limit = limit)
    
    def evaluate_signal(self, bars: pd.DataFrame = None) -> str:
        """
        Evaluate mean reversion condition on bars.

        Returns:
            "buy", "sell", or "hold"
        """
        if bars is None:
            bars = self._get_recent_data()
        
        if bars is None or len(bars) < self.lookback:
            return "hold"
        
        df = bars.copy()
        df["sma"] = df["close"].rolling(window = self.lookback).mean()
        df["std"] = df["close"].rolling(window = self.lookback).std()
        df.dropna(inplace = True)

        if len(df) == 0:
            return "hold"
        
        latest = df.iloc[-1]
        price = latest["close"]
        lower_band = latest["sma"] - self.threshold * latest["std"]
        upper_band = latest["sma"] + self.threshold * latest["std"]

        # contrarian logic
        if price < lower_band:
            return "buy"
        elif price > upper_band:
            return "sell"
        
        return "hold"
    
    def execute_trade(self, signal: str):
        print(f"{self.symbol}: MeanReversion signal = {signal}")