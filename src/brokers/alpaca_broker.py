# src/brokers/alpaca_broker.py

from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from src.brokers.base_broker import BaseBroker
from src.alpaca_client import AlpacaClient


class AlpacaBroker(BaseBroker):
    """Implements the BaseBroker interface for Alpaca via alpaca-py."""

    def __init__(self, paper: bool = True):
        self.client = AlpacaClient(paper=paper)

    def get_account_summary(self):
        account = self.client.get_account()
        return {
            "id": account.id,
            "status": account.status,
            "cash": float(account.cash),
            "portfolio_value": float(account.portfolio_value),
        }

    def get_positions(self):
        positions = self.client.get_positions()
        return [
            {
                "symbol": p.symbol,
                "qty": float(p.qty),
                "market_value": float(p.market_value),
                "unrealized_pl": float(p.unrealized_pl),
            }
            for p in positions
        ]

    def buy(self, symbol: str, qty: int):
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        return self.client.raw_submit_order(order)

    def sell(self, symbol: str, qty: int):
        order = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        return self.client.raw_submit_order(order)

    def list_orders(self, status: str = "open"):
        return self.client.trading.get_orders(status=status)