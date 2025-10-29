import time
from datetime import datetime
from typing import Dict, List, Optional
from threading import Thread, Event

from src.engine.strategy_config import StrategyConfig
from src.engine.scheduler import Scheduler
from src.engine.trade_logger import TradeLogger
from src.data.stock_data_provider import StockDataProvider
from src.data.crypto_data_provider import CryptoDataProvider
from src.brokers.base_broker import BaseBroker
from src.strategies.base_strategy import BaseStrategy
from src.portfolio.risk_config import RiskConfig
from src.portfolio.position_manager import PositionManager

class TradingEngine:
    """
    Main orchestator for automated trading.

    Supports:
    - Multiple strategies on different symbols
    - Concurrent execution
    - Stock (market hours) + Crypto (24/7) trading
    - Paper/live trading via Alpaca
    """

    def __init__(
            self,
            broker: BaseBroker,
            data_provider_stock: StockDataProvider,
            data_provider_crypto: CryptoDataProvider,
            log_dir: str = "logs"
    ):
        """
        Initialize TradingEngine

        Args:
            broker: AlpacaBroker instance for order execution
            data_provider_stock: StockDataProvider instance
            data_provider_crypto: CryptoDataProvider instance
            log_dir: Directory for trade logs
        """
        self.broker = broker
        self.data_provider_stock = data_provider_stock
        self.data_provider_crypto = data_provider_crypto
        self.logger = TradeLogger(log_dir)

        self.strategies: Dict[str, StrategyConfig] = {}
        self.is_running = False
        self.engine_thread: Optional[Thread] = None
        self.stop_event = Event()

    def add_strategy(
            self,
            symbol: str,
            strategy: BaseStrategy,
            risk_config: RiskConfig,
            position_manager: PositionManager,
            interval_seconds: int = 300,
            asset_type: str = "stock"
    ) -> None:
        """
        Register a strategy for automated execution.

        Args:
            symbol: Trading symbol (e.g., "AAPL", "BTC/USD")
            strategy: BaseStrategy instance with evaluate_signal()
            risk_config: RiskConfig instance
            position_manager: PositionManager instance
            interval_seconds: How often to evaluate (default 5 min)
            asset_type: "stock" or "crypto"
        """
        # Validate symbols are the same
        if strategy.symbol != symbol:
            raise ValueError(
                f"Strategy symbol '{strategy.symbol}' "
                f"doesn't match '{symbol}'"
            )
        key = f"{symbol}_{asset_type}"
        config = StrategyConfig(
            symbol = symbol,
            strategy = strategy,
            risk_config = risk_config,
            position_manager = position_manager,
            interval_seconds = interval_seconds,
            asset_type = asset_type
        )

        self.strategies[key] = config
        print(f"Registered strategy: {config}")
    
    def start(self) -> None:
        """
        Start trading engine (non-blocking)/

        Runs main loop in background thread
        """
        if self.is_running:
            print("Engine already running")
            return
        
        self.is_running = True
        self.stop_event.clear()
        self.engine_thread = Thread(target=self._run_loop, daemon = True)
        self.engine_thread.start()
        print("TradingEngine started")
    
    def stop(self) -> None:
        """ Stop trading engine gracefully. """
        if not self.is_running:
            print("Engine not running")
            return
        
        print("Stopping TradingEngine...")
        self.is_running = False
        self.stop_event.set()

        # Wait for thread to finish
        if self.engine_thread:
            self.engine_thread.join(timeout = 5)
        
        print("TradingEngine stopped...")
    
    def _run_loop(self) -> None:
        """ Main event loop (runs in background thread) """
        print("Engine loop started")

        while not self.stop_event.is_set():
            try:
                self._execute_all_strategies()
                time.sleep(1)
            except Exception as e:
                print(f"Error in engine loop: {e}")
    
    def _execute_all_strategies(self) -> None:
        """ Execute all registered strategies if conditions met """
        for key, config in self.strategies.items():
            if not config.enabled:
                continue

            if Scheduler.should_run_strategy(
                asset_type = config.asset_type,
                last_run = config.last_run,
                interval_seconds = config.interval_seconds
            ):
                self._execute_strategy(config)
    
    def _execute_strategy(self, config: StrategyConfig) -> None:
        """
        Execute a single strategy cycle.

        Handles:
        1. Get signal from strategy
        2. Check position exits
        3. Execute trades if signal + space available
        """
        try:
            if config.asset_type == "stock":
                data_provider = self.data_provider_stock
            else:
                data_provider = self.data_provider_crypto
            
            bars = data_provider.get_bars(
                symbol=config.symbol,
                timeframe="1Hour",
                days_back=7,
                limit=200
            )

            if bars is None or len(bars) == 0:
                print(f"⚠ No data for {config.symbol}, skipping this cycle")
                return
            
            print(f"{config.symbol}: Got {len(bars)} bars")
            
            # Evaluate signal
            signal = config.strategy.evaluate_signal(bars=bars)
            print(f"{config.symbol}: Signal = {signal}")

            # Check if we can open new position
            position_mgr = config.position_manager
            current_positions = position_mgr.get_num_open_positions()
            
            # Get account info for position sizing
            account_summary = self.broker.get_account_summary()
            account_value = account_summary["portfolio_value"]

            if signal == "buy":
                # Check if we can open position
                if position_mgr.can_open_position(account_equity=account_value):
                    latest_price = data_provider.get_latest_price(
                        config.symbol
                    )
                    print(f"{config.symbol}: Latest price = ${latest_price:.8f}")

                    # Calculate position size
                    position_size = position_mgr.calculate_position_size(
                        account_equity=account_value,
                        entry_price=latest_price
                    )
                    print(f"{config.symbol}: Position size = {position_size}")

                    if position_size > 0:
                        # Execute buy
                        print(f"Submitting BUY order for {position_size} shares...")
                        order_response = self.broker.buy(config.symbol, position_size)
                        # Get the actual number purchases
                        order_details = self.broker.get_order_details(order_response, config.symbol)
                        filled_qty = order_details['filled_qty']
                        filled_price = order_details['filled_price']
                        order_status = order_details['status']
                        
                        print(
                            f"Order {order_status}: "
                            f"Requested {order_details['qty_requested']}, "
                            f"Filled {filled_qty:.8f} @ ${filled_price:.8f}"
                        )

                        if filled_qty > 0:
                            position_mgr.open_position(
                                symbol=config.symbol,
                                entry_price=filled_price,
                                qty=filled_qty
                            )
                            config.trades_this_session += 1
                            print(
                                f"✅ BUY: {config.symbol} x{filled_qty:.8f} "
                                f"@ ${filled_price:.8f}"
                            )
                        else:
                            print(
                                f"Order not filled for {config.symbol} "
                                f"(status: {order_status})"
                            )
                else:
                    print(
                        f"⚠ Cannot open position on {config.symbol} - "
                        f"limits reached"
                    )
            
            elif signal == "sell":
                # Close existing position if any
                if current_positions > 0:
                    # Verify how many shares we own
                    position = position_mgr.open_positions[0]
                    entry_price = position["entry_price"]
                    entry_qty = position["qty"]
                    print(
                        f"Submitting SELL order for {entry_qty} shares "
                        f"(purchased @ ${entry_price:.8f})"
                    )

                    order_response = self.broker.sell(config.symbol, entry_qty)
                    order_details = self.broker.get_order_details(order_response, config.symbol)

                    exit_qty = order_details["filled_qty"]
                    exit_price = order_details["filled_price"]
                    order_status = order_details["status"]
                    exit_time = datetime.now()

                    print(
                        f"Order {order_status}: "
                        f"Requested {order_details['qty_requested']}, "
                        f"Filled {exit_qty} @ ${exit_price:.8f}"
                    )

                    if exit_qty > 0:
                        position_mgr.close_position(symbol = config.symbol, exit_price = exit_price)
                        pnl = (exit_price - entry_price) * exit_qty
                        pnl_percent = ((exit_price - entry_price) / entry_price) * 100

                        # Log Trade
                        self.logger.log_trade(
                            symbol = config.symbol,
                            entry_price = entry_price,
                            exit_price = exit_price,
                            quantity = exit_qty,
                            exit_time = exit_time,
                            exit_reason = "signal",
                            pnl = pnl,
                            pnl_percent = pnl_percent,
                            entry_time = position["entry_date"]
                        )

                        config.trades_this_session += 1
                        config.pnl_this_session += pnl

                        print(
                            f"SELL EXECUTED: {config.symbol} x{exit_qty} "
                            f"@ ${exit_price:.8f}"
                        )
                        print(
                            f"P&L: ${pnl:.4f} | "
                            f"Session Total: ${config.pnl_this_session:.4f}"
                        )
                    
                    else:
                        print(
                            f"Sell order not filled for {config.symbol} "
                            f"(status: {order_status})"
                        )
            
            config.last_run = datetime.now()

        except Exception as e:
            print(f"❌ Error executing {config.symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    def get_status(self) -> Dict:
        """
        Get current engine status

        Returns:
            Dict with status info
        """
        if not self.strategies:
            return {"is_running": self.is_running, "strategies": {}}
        
        status = {
            "is_running": self.is_running,
            "strategies": {}
        }

        for key, config in self.strategies.items():
            status["strategies"][key] = {
                "symbol": config.symbol,
                "asset_type": config.asset_type,
                "interval": config.interval_seconds,
                "enabled": config.enabled,
                "last_run": config.last_run.isoformat()
                if config.last_run else None,
                "trades_this_session": config.trades_this_session,
                "pnl_this_session": f"${config.pnl_this_session:.2f}"
            }
        
        return status
    
    def print_status(self) -> None:
        """ Pretty print engine status """
        status = self.get_status()
        print("\n" + "="*60)
        print("TRADING ENGINE STATUS")
        print("="*60)
        print(f"Running: {status['is_running']}")
        print(f"Strategies: {len(status['strategies'])}")
        for key, info in status["strategies"].items():
            print(f"\n  {key}:")
            print(f"    Asset Type: {info['asset_type']}")
            print(f"    Interval: {info['interval']}s")
            print(f"    Last Run: {info['last_run']}")
            print(f"    Trades: {info['trades_this_session']}")
        print("="*60 + "\n")
    
    def _get_actual_position_qty(self, symbol: str) -> float:
        """
        Get the actual quantity that we hold from the broker

        Args:
            symbol: Trading symbol (e.g., "XRP/USD")
        
        Returns:
            Actual quantity held, or 0 if none
        """
        positions = self.broker.get_positions()
        print(positions)

        normalized = symbol.replace("/", "")

        for pos in positions:
            if pos["symbol"] == symbol or pos ["symbol"] == normalized:
                return float(pos['qty'])
        
        return 0.0
