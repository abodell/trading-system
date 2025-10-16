from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
import os

class AlpacaClient:
    """ Handles direct connection and low-level operations with Alpaca's API. """

    def __init__(self, paper: bool = True):
        load_dotenv()
        self.api_key = os.getenv("ALPACA_API_KEY")
        self.secret_key = os.getenv("ALPACA_API_SECRET")
        self.base_url = os.getenv("ALPACA_BASE_URL")

        if not all([self.api_key, self.secret_key, self.base_url]):
            raise ValueError("Missing one or more Alpaca environment variables!")
        
        self.trading = TradingClient(self.api_key, self.secret_key, paper = paper)
        self.data = StockHistoricalDataClient(self.api_key, self.secret_key)
    
    def get_account(self):
        """ Return account details (direct from Alpaca). """
        return self.trading.get_account()
    
    def get_positions(self):
        return self.trading.get_all_positions()
    
    def raw_submit_order(self, order_request):
        """ Submit a raw order request (used by higher broker layer). """
        return self.trading.submit_order(order_request)