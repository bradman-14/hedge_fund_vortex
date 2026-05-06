from config import INITIAL_CAPITAL, MAX_POSITION_PCT

class PortfolioState:
    def __init__(self):
        self.cash = INITIAL_CAPITAL
        self.positions = {"Equity": 0, "Oil": 0, "Gold": 0, "Bonds": 0}
        self.history = []  # daily snapshots
    
    def total_value(self, prices: dict) -> float:
        return self.cash + sum(qty * prices[a] for a, qty in self.positions.items())
    
    def max_position_value(self, prices):
        return self.total_value(prices) * MAX_POSITION_PCT
    
    def snapshot(self, date, prices):
        self.history.append({
            "date": date,
            "total_value": self.total_value(prices),
            "cash": self.cash,
            **{f"pos_{k}": v for k, v in self.positions.items()}
        })
