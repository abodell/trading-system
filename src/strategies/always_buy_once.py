from strategies.base_strategy import BaseStrategy

class AlwaysBuyOnce(BaseStrategy):
    """
    Minimal sanity test strategy.
    Buys 1 share the first time it's run, then holds afterward
    """

    def __init__(self, broker, symbol):
        super().__init__(broker, symbol)
        self.has_bought = False
    
    def evaluate_signal(self):
        if not self.has_bought:
            return "buy"
        return "hold"
    
    def execute_trade(self, signal: str):
        if signal == "buy" and not self.has_bought:
            print(f"Placing test BUY for 1 share of {self.symbol}")
            self.broker.buy(self.symbol, 1)
            self.has_bought = True
        else:
            print(f"Holding position for {self.symbol}")