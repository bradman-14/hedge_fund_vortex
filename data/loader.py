import pandas as pd
import os

REQUIRED_COLS = {
    "equity": ["Date","Price","Volume","Returns","SMA_10"],
    "oil": ["Date","Price","Volume","Returns","Volatility"],
    "multi_asset": ["Date","Oil","Gold","Bonds","Oil_Returns","Gold_Returns"],
    "macro": ["Date","Inflation","Interest_Rate","USD_Index","Sentiment"]
}

# Columns to prefix with the dataset key (to avoid collisions on join)
PREFIX_COLS = {
    "equity": {"Price": "equity_Price", "Volume": "equity_Volume", "Returns": "equity_Returns"},
    "oil":    {"Price": "oil_Price",    "Volume": "oil_Volume",    "Returns": "oil_Returns"},
}

def load_all(data_dir="datasets"):
    dfs = {}
    for key, cols in REQUIRED_COLS.items():
        path = f"{data_dir}/{key}_dataset.csv"
        df = pd.read_csv(path, parse_dates=["Date"])
        # Issue 16: schema validation
        missing = set(cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing columns in {key}: {missing}")
        # Rename overlapping columns with dataset prefix
        if key in PREFIX_COLS:
            df = df.rename(columns=PREFIX_COLS[key])
        dfs[key] = df.set_index("Date")
    merged = dfs["equity"].join([dfs["oil"], dfs["multi_asset"], dfs["macro"]], how="inner")
    return merged.reset_index()
