import pandas as pd
from config import LOOKBACK_VOL, MOMENTUM_WINDOW

def engineer_features(df):
    df = df.copy()
    
    # ── Equity Features ──
    df["eq_volatility"] = df["equity_Returns"].rolling(LOOKBACK_VOL).std() * (252**0.5)
    df["eq_momentum"]   = df["equity_Price"].pct_change(MOMENTUM_WINDOW).shift(1)
    df["eq_SMA_ratio"]  = df["equity_Price"] / df["SMA_10"] - 1   # price vs SMA
    
    # ── Oil Features ──
    df["oil_momentum"]  = df["oil_Returns"].rolling(MOMENTUM_WINDOW).mean().shift(1)
    # use pre-computed volatility from dataset directly
    df["oil_vol"]       = df["Volatility"].shift(1)
    
    # ── Gold / Bonds Features (from multi_asset) ──
    df["gold_momentum"] = df["Gold_Returns"].rolling(MOMENTUM_WINDOW).mean().shift(1)
    df["bond_trend"]    = df["Bonds"].pct_change(MOMENTUM_WINDOW).shift(1)
    
    # ── Macro Alignment (already daily, just normalize) ──
    for col in ["Inflation","Interest_Rate","USD_Index","Sentiment"]:
        df[f"macro_{col}"] = (df[col] - df[col].rolling(60).mean()) / df[col].rolling(60).std()
    
    df.dropna(inplace=True)  # drop initial window rows
    return df
