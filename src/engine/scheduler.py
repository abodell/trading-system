import pytz
from datetime import datetime, time
from typing import Tuple

class Scheduler:
    """ Handles market hours detection and scheduling """

    # Market hours: 930AM - 4PM ET
    STOCK_OPEN= time(9, 30)
    STOCK_CLOSE = time(16, 0)

    CRYPTO_ALWAYS_OPEN = True

    @staticmethod
    def is_market_open(asset_type: str) -> bool:
        """
        Check if market is open for asset_type

        Args:
            asset_type: "stock" or "crypto"
        
        Returns:
            bool: True if market is open for trading
        """
        if asset_type.lower() == "crypto":
            return True
        
        if asset_type.lower() == "stock":
            et = pytz.timezone("America/New_York")
            now = datetime.now(et)

            # Saturday or Sunday
            if now.weekday() >= 5:
                return False
            
            # Check market hours
            current_time = now.time()
            return(
                Scheduler.STOCK_OPEN <= current_time < Scheduler.STOCK_CLOSE
            )
        
        raise ValueError(
            f"Unknown asset_type: {asset_type}. "
            "Use 'stock' or 'crypto'"
        )
    
    @staticmethod
    def is_market_closed(asset_type: str) -> bool:
        """ Inverse of is_market_open """
        return not Scheduler.is_market_open(asset_type)
    
    @staticmethod
    def should_run_strategy(
        asset_type: str,
        last_run: datetime = None,
        interval_seconds: int = 300
    ) -> bool:
        """
        Determine if strategy should run now.

        Checks:
        1. Is market open for the asset type?
        2. Has enough time passed since last run?

        Args:
            asset_type: "stock" or "crypto"
            last_run: datetime of last execution
            interval_seconds: minimum seconds between runs
        
        Returns:
            bool: True if strategy should run now
        """
        if not Scheduler.is_market_open(asset_type):
            return False
        
        if last_run is None:
            return True
        
        elapsed = (datetime.now() - last_run).total_seconds()
        return elapsed >= interval_seconds
    