import numpy as np
from config import RISK_FREE_RATE, VAR_CONFIDENCE

def compute_metrics(history_df, market_returns):
    pv = history_df["total_value"].values
    daily_returns = np.diff(pv) / pv[:-1]
    
    # ── Sharpe Ratio ──
    excess = daily_returns - RISK_FREE_RATE / 252
    sharpe = (excess.mean() / excess.std()) * np.sqrt(252) if excess.std() > 0 else 0
    
    # ── Max Drawdown ──
    roll_max = np.maximum.accumulate(pv)
    drawdowns = (pv - roll_max) / roll_max
    max_drawdown = drawdowns.min()
    
    # ── Annualized Volatility ──
    annualized_vol = daily_returns.std() * np.sqrt(252)
    
    # ── VaR (Historical) ──
    var = np.percentile(daily_returns, (1 - VAR_CONFIDENCE) * 100)
    
    # ── Alpha & Beta ──
    mkt = np.array(market_returns[:len(daily_returns)])
    beta = np.cov(daily_returns, mkt)[0,1] / np.var(mkt) if np.var(mkt) > 0 else 0
    alpha = (daily_returns.mean() - beta * mkt.mean()) * 252
    
    # ── Cumulative & Annualized Return ──
    total_return = (pv[-1] - pv[0]) / pv[0]
    n_years = len(pv) / 252
    annualized_return = (1 + total_return) ** (1 / n_years) - 1
    
    return {"sharpe": round(sharpe,4), "max_drawdown": round(max_drawdown,4),
            "volatility": round(annualized_vol,4), "var_95": round(var,4),
            "alpha": round(alpha,4), "beta": round(beta,4),
            "total_return": round(total_return,4), "annualized_return": round(annualized_return,4)}
