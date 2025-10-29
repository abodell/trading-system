import time
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderStatus
from alpaca.trading.models import Order
from src.brokers.base_broker import BaseBroker
from src.alpaca_client import AlpacaClient


class AlpacaBroker(BaseBroker):
    """Implements the BaseBroker interface for Alpaca via alpaca-py."""

    def __init__(self, paper: bool = True):
        self.client = AlpacaClient(paper=paper)
        self._position_before_order = {}

    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol for trading API

        Converts "XRP/USD" -> "XRPUSD" for crypto trading
        Leaves stock symbols unchanged (e.g., "AAPL" -> "AAPL")
        """
        return symbol.replace('/', '')
    
    def _is_crypto(self, symbol: str) -> bool:
        """
        Determine if symbol is crypto based on format

        Crypto symbols contains "/" (e.g, "BTC/USD")
        Stock symbols don't (e.g., "AAPL")
        """
        return "/" in symbol
    
    def _get_time_in_force(self, symbol: str) -> TimeInForce:
        """
        Get appropriate TimeInForce for asset type.

        - Stocks: DAY
        - Crypto: GTC (Good-Til-Canceled)
        """
        if self._is_crypto(symbol):
            return TimeInForce.GTC
        return TimeInForce.DAY

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
        # Get the quantity of this symbol's positions before purchase
        self._position_before_order[symbol] = self._get_position_qty(symbol)

        order = MarketOrderRequest(
            symbol=self._normalize_symbol(symbol),
            qty=qty,
            side=OrderSide.BUY,
            time_in_force=self._get_time_in_force(symbol),
        )
        order_response = self.client.raw_submit_order(order)
        filled_order = self._wait_for_fill(order_response.id)
        
        return filled_order

    def sell(self, symbol: str, qty: int):
        # Get the quantity of this symbol's position before selling
        self._position_before_order[symbol] = self._get_position_qty(symbol)

        order = MarketOrderRequest(
            symbol=self._normalize_symbol(symbol),
            qty=qty,
            side=OrderSide.SELL,
            time_in_force=self._get_time_in_force(symbol),
        )
        order_response = self.client.raw_submit_order(order)
        filled_order = self._wait_for_fill(order_response.id)

        return filled_order

    def list_orders(self, status: str = "open"):
        return self.client.trading.get_orders(status=status)
    
    def _wait_for_fill(self, order_id: str, timeout_seconds: int = 30):
        """
        Poll order status until filled or timeout.

        Args:
            order_id: Order ID to monitor
            timeout_seconds: Max seconds to wait
        
        Returns:
            Filled order object
        """
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            order = self.client.trading.get_order_by_id(order_id)

            if order.status in [
                OrderStatus.FILLED,
                OrderStatus.PARTIALLY_FILLED
            ]:
                return order
            
            time.sleep(0.2)
        
        print(f"Order {order_id} not filled within {timeout_seconds}s")
        return self.client.trading.get_order_by_id(order_id)
    
    def get_order_details(self, order_response: Order, symbol: str) -> dict:
        """
        Extract fill price and quantity from order response.

        For crypto trades Alpaca deducts taker fees from the received asset. We calculate the actual
        filled qty (after fees) by comparing position size before/after the order.

        Returns:
            dict with 'filled_qty' and 'filled_price'
        """
        ordered_qty = (float(order_response.filled_qty) if order_response.filled_qty else 0.0)
        filled_price = (float(order_response.filled_avg_price) if order_response.filled_avg_price else 0.0)

        if self._is_crypto(symbol):
            qty_before = self._position_before_order.get(symbol, 0.0)
            qty_after = self._get_position_qty(symbol)

            if order_response.side == OrderSide.BUY:
                filled_qty = qty_after - qty_before
            else:
                filled_qty = qty_before - qty_after

            # Round quantity for crypto (decimals due to fees)
            filled_qty = round(filled_qty, 8)
            
            if filled_qty < ordered_qty and filled_qty > 0:
                fee_pct = ((ordered_qty - filled_qty) / ordered_qty) * 100
                print(
                    f"Crypto fee applied: "
                    f"ordered {ordered_qty}, received {filled_qty} "
                    f"({fee_pct:.2f}% fee)"
                )
            
            # Clean up
            self._position_before_order.pop(symbol, None)
        
        # If we are trading stock there are no fees
        else:
            filled_qty = (float(order_response.filled_qty) if order_response.filled_qty else 0.0)

        return {
            "filled_qty": filled_qty,
            "filled_price": filled_price,
            "order_id": order_response.id,
            "status": order_response.status,
            "qty_requested": order_response.qty
        }
    
    def _get_position_qty(self, symbol: str) -> float:
        """
        Get actual position quantity from broker.

        Handles both "XRP/USD" and "XRPUSD" formats
        """
        normalized = symbol.replace("/", "")

        for attempt in range(5):
            positions = self.client.get_positions()

            for pos in positions:
                if pos.symbol == symbol or pos.symbol == normalized:
                    return float(pos.qty)
            
            if attempt < 4:
                time.sleep(0.1)
        
        return 0.0
    