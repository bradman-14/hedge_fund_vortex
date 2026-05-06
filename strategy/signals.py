import pandas as pd
from config import SIGNAL_THRESHOLD

def generate_signals(df):
    signals = df[["Date"]].copy()
    
    # ── Equity Signal ──
    cond_buy  = (df["eq_momentum"] > SIGNAL_THRESHOLD) & (df["eq_volatility"] < 0.4)
    cond_sell = (df["eq_momentum"] < -SIGNAL_THRESHOLD)
    signals["Equity"] = "HOLD"
    signals.loc[cond_buy, "Equity"]  = "BUY"
    signals.loc[cond_sell, "Equity"] = "SELL"
    
    # ── Oil Signal ──
    cond_oil_buy  = (df["oil_momentum"] > SIGNAL_THRESHOLD) & (df["oil_vol"] < 0.5)
    cond_oil_sell = (df["oil_momentum"] < -SIGNAL_THRESHOLD)
    signals["Oil"] = "HOLD"
    signals.loc[cond_oil_buy,  "Oil"] = "BUY"
    signals.loc[cond_oil_sell, "Oil"] = "SELL"
    
    # ── Gold Signal (safe-haven: buy when macro_Sentiment < -0.5) ──
    signals["Gold"] = "HOLD"
    signals.loc[df["macro_Sentiment"] < -0.5, "Gold"] = "BUY"
    signals.loc[df["gold_momentum"] > 0.03,   "Gold"] = "SELL"
    
    # ── Bonds Signal ──
    signals["Bonds"] = "HOLD"
    signals.loc[(df["macro_Interest_Rate"] < -0.3) & (df["bond_trend"] > 0), "Bonds"] = "BUY"
    signals.loc[df["macro_Interest_Rate"] > 0.5, "Bonds"] = "SELL"
    
    return signals
