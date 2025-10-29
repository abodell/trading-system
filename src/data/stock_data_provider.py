# src/data/stock_data_provider.py
from datetime import datetime, timedelta, timezone
from typing import Optional, Callable
import pandas as pd

from alpaca.data.live import StockDataStream
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame

from .base_data_provider import BaseDataProvider


def _map_timeframe(tf: str) -> TimeFrame:
    if tf == "1Min":
        return TimeFrame.Minute
    if tf == "5Min":
        return TimeFrame(5, "Min")
    if tf == "15Min":
        return TimeFrame(15, "Min")
    if tf == "1Hour":
        return TimeFrame.Hour
    if tf == "1Day":
        return TimeFrame.Day
    raise ValueError(f"Unsupported timeframe: {tf}")


class StockDataProvider(BaseDataProvider):
    """
    Unified stock data provider with both real-time and historical data.
    Real-time via WebSocket (IEX under Basic plan) + historical bars via REST.
    """

    def __init__(self, api_key: str, secret_key: str):
        self.stream = StockDataStream(api_key, secret_key)
        self.hist = StockHistoricalDataClient(api_key, secret_key)

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """ Get the latest ask price (what we'd pay to buy) """
        try:
            req = StockLatestQuoteRequest(symbol_or_symbols = symbol)
            res = self.hist.get_stock_latest_quote(req)

            if symbol in res:
                quote = res[symbol]
                return float(quote.ask_price)
            return None
        except Exception:
            return None


    def get_bars(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        days_back: int = 7,
    ) -> pd.DataFrame:
        """
        Get historical bars for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            timeframe: Bar timeframe ("1Min", "5Min", "15Min", "1Hour", "1Day")
            limit: Max number of bars to return
            days_back: How many days back to fetch data from
        """
        tf = _map_timeframe(timeframe)
        now = datetime.now(timezone.utc)

        # Buffer end for intraday frames to avoid incomplete bar edge cases
        if tf in (
            TimeFrame.Minute,
            TimeFrame(5, "Min"),
            TimeFrame(15, "Min"),
            TimeFrame.Hour,
        ):
            end = now - timedelta(minutes=2)
        else:
            # Daily bars: buffer by 15 minutes
            end = now - timedelta(minutes=15)

        start = end - timedelta(days=days_back)

        req = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start,
            end=end,
            limit=limit,
        )
        df = self.hist.get_stock_bars(req).df
        if df.empty:
            return df
        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(symbol)
        df = df.sort_index()
        return df[["open", "high", "low", "close", "volume"]].copy()

    def on_quote(self, symbol: str, handler: Callable):
        """Subscribe to quote updates (async handler required)"""
        self.stream.subscribe_quotes(handler, symbol)

    def on_trade(self, symbol: str, handler: Callable):
        """Subscribe to trade updates (async handler required)"""
        self.stream.subscribe_trades(handler, symbol)

    def start(self):
        """Start the WebSocket stream. Blocks until stop() is called."""
        self.stream.run()

    def stop(self):
        """Stop the WebSocket stream (synchronous)."""
        self.stream.stop()