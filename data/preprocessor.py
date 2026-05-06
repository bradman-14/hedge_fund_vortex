import numpy as np

def preprocess(df):
    df = df.copy().sort_values("Date").reset_index(drop=True)
    
    # 1. Forward-fill NaNs (no look-ahead bias)
    df.ffill(inplace=True)
    df.bfill(inplace=True)  # only for initial rows with no prior data
    
    # 2. Clip outliers at ±3 std per numeric column
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        mean, std = df[col].mean(), df[col].std()
        df[col] = df[col].clip(mean - 3*std, mean + 3*std)
    
    # 3. Remove duplicate dates
    df = df.drop_duplicates(subset="Date")
    
    return df
