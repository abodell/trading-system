from src.strategies.base_strategy import BaseStrategy
from src.data.base_data_provider import BaseDataProvider
import pandas as pd
import pandas_ta as ta

class MACDStrategy(BaseStrategy):
    """
    Moving Average Convergence Divergence (MACD) Trend-Following Strategy.

    - Uses EMA fast/slow differentials to capture momentum.
    - Generates buy when MACD crosses above signal line.
    - Generates sell when MACD crosses below signal line.
    """

    def __init__(
            self,
            broker,
            symbol: str,
            data_provider: BaseDataProvider,
            fast: int = 12,
            slow: int = 26,
            signal: int = 9,
    ):
        super().__init__(broker, symbol)
        self.data_provider = data_provider
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def _get_recent_data(self, bars_back: int = 100) -> pd.DataFrame:
        """ Fetch recent bars for indicator calculation """
        data = self.data_provider.get_bars(
            symbol=self.symbol, timeframe="1Day", limit=bars_back
        )
        return data
    
    def evaluate_signal(self, bars: pd.DataFrame = None) -> str:
        """
        Evaluate MACD crossovers.

        Args:
            bars: Optional DataFrame of bars. If None, fetch from data_provider
        Returns:
            "buy", "sell", or "hold"
        """
        if bars is None:
            bars = self._get_recent_data()
        
        if bars is None or len(bars) < self.slow + self.signal:
            return "hold"
        
        df = bars.copy()
        macd_df = ta.macd(df["close"], fast = self.fast, slow = self.slow, signal = self.signal)

        df["macd"] = macd_df.iloc[:, 0]
        df["signal_line"] = macd_df.iloc[:, 1]

        # Check latest two points for crossover
        recent = df.iloc[-1]
        prev = df.iloc[-2]

        if pd.notna(prev["macd"]) and pd.notna(prev["signal_line"]):
            # Bullish cross: MACD below then above signal
            if prev.macd < prev.signal_line and recent.macd > recent.signal_line:
                return "buy"
            # Bearish: MACD above then below signal
            if prev.macd > prev.signal_line and recent.macd < recent.signal_line:
                return "sell"

        return "hold"
    
    def execute_trade(self, signal: str):
        print(f"{self.symbol}: MACD signal = {signal}")