# src/strategies/simple_sma.py
from strategies.base_strategy import BaseStrategy
import pandas as pd

class SimpleSMA(BaseStrategy):
    def __init__(self, broker, symbol, data_provider, short_window=5, long_window=20):
        super().__init__(broker, symbol)
        self.data = data_provider
        self.short_window = short_window
        self.long_window = long_window

    def _get_recent_data(self) -> pd.DataFrame:
        limit = max(self.long_window + 5, 40)
        return self.data.get_bars(self.symbol, "1Day", limit=limit)

    def evaluate_signal(self) -> str:
        data = self._get_recent_data()
        if data.empty or len(data) < self.long_window + 1:
            return "hold"

        data["sma_short"] = data["close"].rolling(self.short_window).mean()
        data["sma_long"] = data["close"].rolling(self.long_window).mean()

        recent = data.iloc[-1]
        prev = data.iloc[-2]

        if pd.notna(prev.sma_short) and pd.notna(prev.sma_long):
            if prev.sma_short < prev.sma_long and recent.sma_short > recent.sma_long:
                return "buy"
            if prev.sma_short > prev.sma_long and recent.sma_short < recent.sma_long:
                return "sell"
        return "hold"

    def execute_trade(self, signal: str):
        print(f"Signal for {self.symbol}: {signal}")
        if signal == "buy":
            self.broker.buy(self.symbol, 1)
        elif signal == "sell":
            self.broker.sell(self.symbol, 1)