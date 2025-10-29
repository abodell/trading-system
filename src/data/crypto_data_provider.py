from typing import Optional, Callable
import pandas as pd

from alpaca.data.live import CryptoDataStream
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, CryptoLatestQuoteRequest
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

class CryptoDataProvider(BaseDataProvider):
    """
    Real-time crypto via WebSocket + historical pulls for indicators
    Symbols should be in format: "BTC/USD", "ETH/USD", etc.
    """

    def __init__(self, api_key: str, secret_key: str):
        self.stream = CryptoDataStream(api_key, secret_key)
        self.hist = CryptoHistoricalDataClient(api_key, secret_key)
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """ Get latest ask price (what we'd pay to buy) """
        try:
            req = CryptoLatestQuoteRequest(symbol_or_symbols = symbol)
            res = self.hist.get_crypto_latest_quote(req)

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
            symbol: Crypto symbol (e.g., "BTC/USD")
            timeframe: Bar timeframe ("1Min", "5Min", "15Min", "1Hour", "1Day")
            limit: Max number of bars to return
            days_back: How many days back to fetch data from
        """
        from datetime import datetime, timedelta, timezone
        
        tf = _map_timeframe(timeframe)
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=days_back)
        
        req = CryptoBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start,
            end=now,
            limit=limit,
        )
        df = self.hist.get_crypto_bars(req).df
        if df.empty:
            return df
        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(symbol)
        df = df.sort_index()
        return df[["open", "high", "low", "close", "volume"]].copy()
    
    def on_quote(self, symbol: str, handler: Callable):
        """ Subscribe to quote updates (async handler required) """
        self.stream.subscribe_quotes(handler, symbol)
    
    def on_trade(self, symbol: str, handler: Callable):
        """ Subscibe to trade updates (async handler required) """
        self.stream.subscribe_trades(handler, symbol)
    
    def start(self):
        """ Start the WebSocket stram. Blocks until stop() is called. """
        self.stream.run()
    
    def stop(self):
        """ Stop the WebSocket stram (synchronous) """
        self.stream.stop()