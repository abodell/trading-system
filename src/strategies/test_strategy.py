from src.strategies.base_strategy import BaseStrategy
from src.data.base_data_provider import BaseDataProvider
import pandas as pd

class TestStrategy(BaseStrategy):
    """
    Test strategy that generates predictable buy / sell signals for faster testing

    Used to validate TradingEngine pipeline without waiting for real market signals. Cycles through: Buy -> Hold -> Sell -> Hold
    """

    def __init__(self, broker, symbol, data_provider: BaseDataProvider):
        super().__init__(broker, symbol)
        self.data = data_provider
        self.call_count = 0
    
    def evaluate_signal(self, bars: pd.DataFrame = None) -> str:
        """
        Generate signals in a predicatable pattern for testing

        Cycle: BUY (1x) -> HOLD(1x) -> SELL(1x) -> HOLD(1x) -> repeat
        """
        signals = ['buy', 'hold', 'sell', 'hold']
        signal = signals[self.call_count % len(signals)]
        self.call_count += 1

        print(f"TestStrategy call #{self.call_count}: returning '{signal}'")
        return signal
    
    def execute_trade(self, signal: str):
        """ Not used by TradingEngine but required by BaseStrategy """
        pass


