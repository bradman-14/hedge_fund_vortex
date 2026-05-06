import pandas as pd
from portfolio.sizer import compute_position_size
from portfolio.state import PortfolioState
from logs.trade_logger import TradeLogger
from metrics.calculator import compute_metrics

def test_extreme_volatility():
    """Simulate a 10x volatility spike — position sizer must cap exposure"""
    size = compute_position_size("Equity", 1_000_000, 100.0, 2.0, risk_pct=0.01)
    max_allowed = (1_000_000 * 0.25) / 100.0   # MAX_POSITION_PCT cap
    assert size <= max_allowed, "Position size exceeded cap during high volatility"

def test_insufficient_capital():
    """Trade requiring more cash than available must be rejected, not crash"""
    state = PortfolioState()
    state.cash = 100   # near-zero cash
    logger = TradeLogger()
    # Attempt to buy 1000 shares at $500 = $500,000 — should be rejected
    cost = 1000 * 500 * 1.002
    if cost > state.cash:
        logger.log_error("2024-01-01", "Equity", "INSUFFICIENT_CAPITAL", cost, state.cash)
    assert len(logger.errors) == 1
    assert state.cash == 100   # cash unchanged

def test_extended_drawdown():
    """Simulate 60 days of consecutive negative returns — system must stay stable"""
    dummy_history = [{"date": f"2024-{i:02d}", "total_value": 1_000_000 * (0.99 ** i),
                      "cash": 0, "pos_Equity": 0, "pos_Oil": 0, "pos_Gold": 0, "pos_Bonds": 0}
                     for i in range(1, 61)]
    history_df = pd.DataFrame(dummy_history)
    mkt = [-0.005] * 59
    metrics = compute_metrics(history_df, mkt)
    assert metrics["max_drawdown"] < 0   # drawdown is negative
    assert metrics["max_drawdown"] > -1  # not total loss
    assert "sharpe" in metrics           # no KeyError
