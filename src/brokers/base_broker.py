from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseBroker(ABC):
    """
    Abstract base class defining the Broker Interface for all trading backends.
    This ensures a consistent API across different broker implementations
    (Alpaca, Binance, Interactive Brokers, Backtesting, etc.)
    """

    @abstractmethod
    def get_account_summary(self) -> Dict[str, Any]:
        """ Return information about the current trading account. """
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """ Return all open positions. """
        pass

    @abstractmethod
    def buy(self, symbol: str, qty: int) -> Any:
        """ Place a market buy order. """
        pass

    @abstractmethod
    def sell(self, symbol: str, qty: int) -> Any:
        """ Place a market sell order. """
        pass

    @abstractmethod
    def list_orders(self, status: str = "open") -> List[Any]:
        """ List orders by status (open, closed, canceled, etc.) """
        pass

    def __enter__(self):
        """ Optional context manager support. """
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Optional cleanup hook (close connections, etc.) """
        pass