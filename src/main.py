# src/main.py
import threading
import time
from collections import defaultdict

from brokers.alpaca_broker import AlpacaBroker
from data.stock_data_provider import StockDataProvider
from strategies.simple_sma import SimpleSMA

SYMBOLS = ["AAPL", "MSFT", "NVDA"]


def test_stock_historical():
    """Test historical data and strategy"""
    broker = AlpacaBroker(paper=True)
    print("=== Testing Stock Historical Data ===")
    print(broker.get_account_summary())
    print()

    provider = StockDataProvider(
        api_key=broker.client.api_key,
        secret_key=broker.client.secret_key,
    )

    # Test 1: Latest prices
    print("=== Latest Prices ===")
    for sym in SYMBOLS:
        price = provider.get_latest_price(sym)
        print(f"{sym}: ${price}")
    print()

    # Test 2: Daily bars
    print("=== Hourly Bars (last 3 days by hour) ===")
    for sym in SYMBOLS:
        df = provider.get_bars(sym, "1Hour", limit=100, days_back=3)
        if not df.empty:
            print(f"\n{sym}:")
            print(df[["open", "close", "volume"]])
    print()

    # Test 3: SimpleSMA strategy
    print("=== Testing SimpleSMA on AAPL ===")
    sma_strategy = SimpleSMA(broker, "AAPL", data_provider=provider)
    signal = sma_strategy.evaluate_signal()
    print(f"Signal: {signal}")

    data = sma_strategy._get_recent_data()
    data["sma_short"] = data["close"].rolling(
        sma_strategy.short_window
    ).mean()
    data["sma_long"] = data["close"].rolling(
        sma_strategy.long_window
    ).mean()
    print("\nRecent data with SMAs:")
    print(data[["close", "sma_short", "sma_long"]].tail(10))


def test_stock_realtime():
    """Test real-time WebSocket stream"""
    broker = AlpacaBroker(paper=True)
    print("=== Testing Stock Real-Time Stream ===")
    print(broker.get_account_summary())
    print()

    provider = StockDataProvider(
        api_key=broker.client.api_key,
        secret_key=broker.client.secret_key,
    )

    tick_counts = defaultdict(int)
    stop_flag = {"stop": False}
    MAX_TICKS_PER_SYMBOL = 10
    STREAM_TIMEOUT_SECONDS = 30

    async def on_quote(quote):
        try:
            sym = quote.symbol
            tick_counts[sym] += 1
            print(
                f"[QUOTE] {sym} bid=${quote.bid_price:.2f} "
                f"ask=${quote.ask_price:.2f} | count={tick_counts[sym]}"
            )
            if all(
                tick_counts[s] >= MAX_TICKS_PER_SYMBOL for s in SYMBOLS
            ):
                print("\nReached max ticks per symbol, stopping...")
                provider.stop()
                stop_flag["stop"] = True
        except Exception as e:
            print(f"Quote handler error: {e}")

    print("Subscribing to quotes...")
    for sym in SYMBOLS:
        provider.on_quote(sym, on_quote)

    def timeout_stop():
        time.sleep(STREAM_TIMEOUT_SECONDS)
        if not stop_flag["stop"]:
            print(f"\nTimeout reached, stopping stream...")
            provider.stop()
            stop_flag["stop"] = True

    t = threading.Thread(target=timeout_stop, daemon=True)
    t.start()

    print(f"Starting stream (will stop after {MAX_TICKS_PER_SYMBOL} "
          f"ticks per symbol or {STREAM_TIMEOUT_SECONDS}s)...\n")
    try:
        provider.start()
    except Exception as e:
        print(f"Stream error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "realtime":
        print("Note: Real-time only works during market hours (9:30 AM - 4:00 PM ET)\n")
        test_stock_realtime()
    else:
        test_stock_historical()