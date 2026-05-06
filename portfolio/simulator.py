from config import TRANSACTION_COST, SLIPPAGE, REBALANCE_FREQ
from portfolio.sizer import compute_position_size

def rebalance(state, prices, logger, date):
    # Simple rebalancing: we could re-calculate position sizes or do nothing
    pass

def simulate(df_features, signals, state, logger):
    prices_cols = {"Equity":"equity_Price","Oil":"oil_Price","Gold":"Gold","Bonds":"Bonds"}
    vol_cols    = {"Equity":"eq_volatility","Oil":"oil_vol","Gold":"eq_volatility","Bonds":"eq_volatility"}
    
    for i, row in df_features.iterrows():
        prices = {a: row[c] for a, c in prices_cols.items()}
        state.snapshot(row["Date"], prices)
        sig_row = signals.loc[signals["Date"] == row["Date"]].iloc[0]
        portfolio_val = state.total_value(prices)
        
        for asset in ["Equity","Oil","Gold","Bonds"]:
            signal = sig_row[asset]
            price  = prices[asset]
            vol    = row.get(vol_cols[asset], 0.2)
            
            if signal == "BUY" and state.positions[asset] == 0:
                qty = compute_position_size(asset, portfolio_val, price, vol)
                cost = qty * price * (1 + TRANSACTION_COST + SLIPPAGE)
                if cost > state.cash:          # Issue 15: insufficient capital
                    logger.log_error(row["Date"], asset, "INSUFFICIENT_CAPITAL", cost, state.cash)
                    continue
                state.cash -= cost
                state.positions[asset] += qty
                logger.log_trade(row["Date"], asset, "BUY", qty, price, vol, sig_row)
            
            elif signal == "SELL" and state.positions[asset] > 0:
                qty = state.positions[asset]
                proceeds = qty * price * (1 - TRANSACTION_COST - SLIPPAGE)
                state.cash += proceeds
                state.positions[asset] = 0
                logger.log_trade(row["Date"], asset, "SELL", qty, price, vol, sig_row)
        
        # Monthly rebalancing
        if i % REBALANCE_FREQ == 0:
            rebalance(state, prices, logger, row["Date"])
    
    return state
