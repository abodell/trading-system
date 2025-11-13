from typing import List
from src.strategies.base_strategy import BaseStrategy

class StrategyEnsemble(BaseStrategy):
    """
    Combines multiple strategies and generates a single consensus signal.
    Static inclusion: all strategies participate equally.
    """

    def __init__(self, broker, symbol, strategies: List[BaseStrategy] = None, min_votes: int = 2, verbose: bool = False):
        super().__init__(broker, symbol)
        self.strategies = strategies
        self.verbose = verbose
        self.min_votes = min_votes
    
    def evaluate_signal(self, bars):
        """
        Call evaluate_signal() on each strategy and combine their votes.
        Static inclusion: equal weight for all strategies.
        """
        signals = []
        for strat in self.strategies:
            try:
                sig = strat.evaluate_signal(bars)
                signals.append(sig)
            except Exception as e:
                if self.verbose:
                    print(f"[WARN] {strat.__class__.__name__} signal fialed: {e}")
                signals.append("hold")
        
        buy_votes = signals.count("buy")
        sell_votes = signals.count("sell")

        if buy_votes >= self.min_votes and buy_votes > sell_votes:
            decision = "buy"
        elif sell_votes >= self.min_votes and sell_votes > buy_votes:
            decision = "sell"
        else:
            decision = "hold"
        
        if self.verbose:
            print(f"[ENSEMBLE] buy={buy_votes}, sell={sell_votes}, hold={signals.count('hold')} -> {decision}")
        
        return decision
    
    def execute_trade(self, signal: str):
        print(f"{self.symbol}: STRATEGY ENSEMBLE signal = {signal}")