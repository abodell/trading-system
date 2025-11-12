from src.strategies.base_strategy import BaseStrategy
from src.data.base_data_provider import BaseDataProvider
import pandas as pd
import pandas_ta as ta

class RSIStrategy(BaseStrategy):
    """
    Relative Strength Index (RSI) mean-reversion strategy.

    Buys when RSI < oversold threshold
    Sells when RSI > overbought threshold.
    Holds otherwise
    """

    def __init__(
            self,
            broker,
            symbol: str,
            data_provider: BaseDataProvider,
            period: int = 14,
            overbought: int = 70,
            oversold: int = 30,
    ):
        super().__init__(broker, symbol)
        self.data_provider = data_provider
        self.period = period
        self.overbought = overbought
        self.oversold = oversold
    
    def _get_recent_data(self, bars_back: int = 100) -> pd.DataFrame:
        """ Fetch recent bars (default 100) for indicator calculation. """
        data = self.data_provider.get_bars(
            symbol = self.symbol, timeframe = "1Day", limit = bars_back
        )
        return data
    
    def evaluate_signal(self, bars: pd.DataFrame = None) -> str:
        """
        Evaluate RSI crossover conditions.

        Args:
            bars: Optional market data DataFrame for backtesting
        Returns:
            "buy", "sell", or "hold"
        """
        if bars is None:
            bars = self._get_recent_data()
        
        if bars is None or len(bars) < self.period + 1:
            return "hold"
        
        df = bars.copy()
        df['rsi'] = ta.rsi(df['close'], length = self.period)

        latest_rsi = df['rsi'].iloc[-1]

        if latest_rsi < self.oversold:
            return "buy"
        elif latest_rsi > self.overbought:
            return "sell"
        
        return "hold"
    
    def execute_trade(self, signal: str):
        """
        TradingEngine will handle execution
        """
        print(f"{self.symbol}: RSI signal = {signal}")