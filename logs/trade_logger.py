import pandas as pd

class TradeLogger:
    def __init__(self):
        self.trades = []
        self.errors = []
    
    def log_trade(self, date, asset, action, qty, price, volatility, signal_row):
        self.trades.append({
            "date": date, "asset": asset, "action": action,
            "quantity": round(qty, 2), "price": round(price, 4),
            "volatility": round(volatility, 4),
            "rationale": f"{action} triggered: momentum={signal_row.get('eq_momentum','N/A')}, vol={volatility:.4f}"
        })
    
    def log_error(self, date, asset, error_type, required, available):
        self.errors.append({
            "date": date, "asset": asset, "error": error_type,
            "required_cash": round(required, 2), "available_cash": round(available, 2)
        })
    
    def to_dataframe(self):
        return pd.DataFrame(self.trades)
    
    def save(self, path="trade_log.csv"):
        self.to_dataframe().to_csv(path, index=False)
