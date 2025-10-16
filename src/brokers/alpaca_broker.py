from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca_client import AlpacaClient

class AlpacaBroker:
    """ Higher-level broker abstraction built on top of AlpacaClient. """

    def __init__(self, paper: bool = True):
        self.client = AlpacaClient(paper = paper)
    
    def get_account_summary(self):
        acc = self.client.get_account()
        return {
            "id": acc.id,
            "cash": float(acc.cash),
            "portfolio_value": float(acc.portfolio_value),
            "status": acc.status
        }
    
    def buy(self, symbol: str, qty: int):
        order = MarketOrderRequest(
            symbol = symbol, qty = qty, side = OrderSide.BUY,
            time_in_force = TimeInForce.DAY
        )
        return self.client.raw_submit_order(order)
    
    def sell(self, symbol: str, qty: int):
        order = MarketOrderRequest(
            symbol = symbol, qty = qty, side = OrderSide.SELL,
            time_in_force = TimeInForce.DAY
        )
        return self.client.raw_submit_order(order)