from abc import ABC, abstractmethod
from src.brokers.base_broker import BaseBroker

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies
    Each strategy defines how it evaluates signals
    and optionally executes trades through the broker.
    """

    def __init__(self, broker: BaseBroker, symbol: str):
        self.broker = broker
        self.symbol = symbol

    @abstractmethod
    def evaluate_signal(self) -> str:
        """
        Determine trading signal.

        Should return one of: "buy", "sell", "hold"
        This method **does not** actually execute trades;
        it only decides *what* should be done
        """
        pass

    @abstractmethod
    def execute_trade(self, signal: str):
        """
        Executes a trade via the broker based on a given signal

        The strategy decides how to translate signals
        into actual trades (e.g, quantity sizing, limits, etc)
        """
        pass

    def run_once(self):
        """
        Evaluate and act on one strategy cycle.
        This is the main entry point for execution loops.
        """
        signal = self.evaluate_signal()
        self.execute_trade(signal)
    