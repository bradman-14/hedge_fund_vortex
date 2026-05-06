from config import MAX_POSITION_PCT

def compute_position_size(asset, portfolio_value, asset_price, asset_volatility, risk_pct=0.01):
    """
    risk_pct: % of portfolio risked per trade (default 1%)
    dollar_risk = portfolio_value * risk_pct
    shares = dollar_risk / (asset_price * asset_volatility)
    capped at MAX_POSITION_PCT of portfolio
    """
    if asset_volatility <= 0 or asset_price <= 0:
        return 0
    dollar_risk = portfolio_value * risk_pct
    shares = dollar_risk / (asset_price * asset_volatility)
    max_shares = (portfolio_value * MAX_POSITION_PCT) / asset_price
    return min(shares, max_shares)
