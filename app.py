import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from data.loader import load_all
from data.preprocessor import preprocess
from features.engineer import engineer_features
from strategy.signals import generate_signals
from portfolio.state import PortfolioState
from portfolio.simulator import simulate
from metrics.calculator import compute_metrics
from logs.trade_logger import TradeLogger
import os

# ──────────────────────────────────────────────
# Page Config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Vortex Hedge Fund Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Custom CSS for premium look
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #141e30 50%, #1a1a2e 100%);
    }
    /* Metric cards */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 16px;
        backdrop-filter: blur(10px);
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
    }
    /* Header */
    h1 {
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
    }
    /* Divider */
    hr {
        border-color: rgba(255,255,255,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Title & Subtitle
# ──────────────────────────────────────────────
st.title("🌀 Vortex Hedge Fund Dashboard")
st.caption("Risk Modeling & Semi-Automated Trading System  •  Code2Create Challenge Round 3")
st.divider()

# ──────────────────────────────────────────────
# Pipeline Execution (cached)
# ──────────────────────────────────────────────
@st.cache_data
def run_pipeline():
    df = load_all()
    df = preprocess(df)
    df = engineer_features(df)
    signals = generate_signals(df)
    state = PortfolioState()
    logger = TradeLogger()
    state = simulate(df, signals, state, logger)
    history = pd.DataFrame(state.history)
    market_returns = df["equity_Returns"].dropna().values
    metrics = compute_metrics(history, market_returns)
    return df, history, signals, logger.to_dataframe(), pd.DataFrame(logger.errors), metrics

try:
    df_features, history, signals, trades, errors, metrics = run_pipeline()
except Exception as e:
    st.error(f"⚠️ Pipeline error: {e}")
    st.info("Please ensure all 4 CSV datasets are in the `datasets/` folder.")
    st.stop()

# ──────────────────────────────────────────────
# Sidebar — Filters & Info
# ──────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/combo-chart.png", width=64)
    st.header("Controls")
    
    date_min = pd.to_datetime(history["date"]).min().date()
    date_max = pd.to_datetime(history["date"]).max().date()
    date_range = st.date_input("Date Range", value=(date_min, date_max), min_value=date_min, max_value=date_max)
    
    selected_assets = st.multiselect("Assets", ["Equity", "Oil", "Gold", "Bonds"], default=["Equity", "Oil", "Gold", "Bonds"])
    
    st.divider()
    st.subheader("📊 Quick Stats")
    st.metric("Total Trading Days", f"{len(history):,}")
    st.metric("Total Trades", f"{len(trades):,}")
    st.metric("Capital Errors", f"{len(errors):,}")
    st.divider()
    st.caption("Built for Code2Create Challenge R3")

# Filter history by date range
if len(date_range) == 2:
    mask = (pd.to_datetime(history["date"]).dt.date >= date_range[0]) & \
           (pd.to_datetime(history["date"]).dt.date <= date_range[1])
    history_filtered = history[mask].copy()
else:
    history_filtered = history.copy()

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Portfolio", "🛡️ Risk Metrics", "🥧 Allocation", "⚖️ Alpha / Beta", "📋 Trade Log"])

# ═══════════════════════════════════════════════
# TAB 1 — Portfolio Overview
# ═══════════════════════════════════════════════
with tab1:
    st.subheader("Portfolio Value Over Time")
    
    # Top-level metrics
    c1, c2, c3, c4 = st.columns(4)
    start_val = history_filtered["total_value"].iloc[0]
    end_val = history_filtered["total_value"].iloc[-1]
    total_ret = (end_val - start_val) / start_val
    c1.metric("Starting Value", f"${start_val:,.0f}")
    c2.metric("Current Value", f"${end_val:,.0f}")
    c3.metric("Total Return", f"{total_ret:.2%}", delta=f"{total_ret:.2%}")
    c4.metric("Sharpe Ratio", f"{metrics['sharpe']:.4f}")
    
    # Portfolio value line chart
    fig_pv = go.Figure()
    fig_pv.add_trace(go.Scatter(
        x=history_filtered["date"], y=history_filtered["total_value"],
        mode="lines", name="Portfolio Value",
        line=dict(color="#00d2ff", width=2),
        fill="tozeroy", fillcolor="rgba(0,210,255,0.08)"
    ))
    
    # Add BUY/SELL markers from trades
    if not trades.empty:
        buys = trades[trades["action"] == "BUY"]
        sells = trades[trades["action"] == "SELL"]
        
        # Map trade dates to portfolio values
        date_to_val = dict(zip(history["date"].astype(str), history["total_value"]))
        
        buy_dates = buys["date"].astype(str).tolist()
        buy_vals = [date_to_val.get(d, None) for d in buy_dates]
        sell_dates = sells["date"].astype(str).tolist()
        sell_vals = [date_to_val.get(d, None) for d in sell_dates]
        
        fig_pv.add_trace(go.Scatter(
            x=buy_dates, y=buy_vals,
            mode="markers", name="BUY",
            marker=dict(color="#00e676", size=5, symbol="triangle-up"),
        ))
        fig_pv.add_trace(go.Scatter(
            x=sell_dates, y=sell_vals,
            mode="markers", name="SELL",
            marker=dict(color="#ff1744", size=5, symbol="triangle-down"),
        ))
    
    fig_pv.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=500,
        xaxis_title="Date", yaxis_title="Portfolio Value ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(l=40, r=20, t=40, b=40),
    )
    st.plotly_chart(fig_pv, width="stretch")
    
    # Cash over time
    st.subheader("Cash Balance Over Time")
    fig_cash = px.area(history_filtered, x="date", y="cash",
                       template="plotly_dark", color_discrete_sequence=["#7c4dff"])
    fig_cash.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           height=300, margin=dict(l=40, r=20, t=20, b=40))
    st.plotly_chart(fig_cash, width="stretch")


# ═══════════════════════════════════════════════
# TAB 2 — Risk Metrics
# ═══════════════════════════════════════════════
with tab2:
    st.subheader("Risk Dashboard")
    
    # Metric cards row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sharpe Ratio", f"{metrics['sharpe']:.4f}")
    m2.metric("Max Drawdown", f"{metrics['max_drawdown']:.2%}")
    m3.metric("VaR (95% daily)", f"{metrics['var_95']:.2%}")
    m4.metric("Ann. Volatility", f"{metrics['volatility']:.2%}")
    
    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Total Return", f"{metrics['total_return']:.2%}")
    m6.metric("Ann. Return", f"{metrics['annualized_return']:.2%}")
    m7.metric("Alpha", f"{metrics['alpha']:.4f}")
    m8.metric("Beta", f"{metrics['beta']:.4f}")
    
    st.divider()
    
    # Drawdown chart
    st.subheader("Drawdown Over Time")
    pv = history_filtered["total_value"].values
    roll_max = np.maximum.accumulate(pv)
    drawdown_series = (pv - roll_max) / roll_max
    dd_df = pd.DataFrame({"date": history_filtered["date"].values, "drawdown": drawdown_series})
    
    fig_dd = go.Figure()
    fig_dd.add_trace(go.Scatter(
        x=dd_df["date"], y=dd_df["drawdown"],
        mode="lines", name="Drawdown",
        line=dict(color="#ff1744", width=1.5),
        fill="tozeroy", fillcolor="rgba(255,23,68,0.15)"
    ))
    fig_dd.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=350, yaxis_tickformat=".1%",
        yaxis_title="Drawdown", xaxis_title="Date",
        margin=dict(l=40, r=20, t=20, b=40),
    )
    st.plotly_chart(fig_dd, width="stretch")
    
    # Daily returns distribution
    st.subheader("Daily Returns Distribution")
    daily_rets = np.diff(pv) / pv[:-1]
    fig_hist = px.histogram(x=daily_rets, nbins=100, template="plotly_dark",
                            color_discrete_sequence=["#3a7bd5"], labels={"x": "Daily Return"})
    fig_hist.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           height=300, showlegend=False,
                           margin=dict(l=40, r=20, t=20, b=40))
    fig_hist.add_vline(x=np.percentile(daily_rets, 5), line_dash="dash", line_color="#ff1744",
                       annotation_text="VaR 95%")
    st.plotly_chart(fig_hist, width="stretch")


# ═══════════════════════════════════════════════
# TAB 3 — Asset Allocation
# ═══════════════════════════════════════════════
with tab3:
    st.subheader("Current Asset Allocation")
    
    # Latest positions
    last_row = history_filtered.iloc[-1]
    pos_cols = [c for c in history.columns if c.startswith("pos_")]
    latest_prices = {
        "Equity": df_features["equity_Price"].iloc[-1],
        "Oil": df_features["oil_Price"].iloc[-1],
        "Gold": df_features["Gold"].iloc[-1],
        "Bonds": df_features["Bonds"].iloc[-1],
    }
    
    alloc = {}
    for col in pos_cols:
        asset_name = col.replace("pos_", "")
        qty = last_row[col]
        if asset_name in latest_prices:
            alloc[asset_name] = qty * latest_prices[asset_name]
    alloc["Cash"] = last_row["cash"]
    
    # Filter out zero/negligible values for the pie
    alloc_filtered = {k: max(v, 0) for k, v in alloc.items() if v > 0.01}
    
    col_pie, col_bar = st.columns(2)
    
    with col_pie:
        if alloc_filtered:
            fig_pie = px.pie(
                names=list(alloc_filtered.keys()),
                values=list(alloc_filtered.values()),
                template="plotly_dark",
                color_discrete_sequence=["#00d2ff", "#3a7bd5", "#7c4dff", "#ff6d00", "#00e676"],
                hole=0.45,
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", height=400,
                margin=dict(l=20, r=20, t=30, b=20),
                title="Portfolio Composition"
            )
            st.plotly_chart(fig_pie, width="stretch")
        else:
            st.info("No active positions.")
    
    with col_bar:
        # Position value over time
        pos_value_df = history_filtered[["date"]].copy()
        for asset in selected_assets:
            pcol = f"pos_{asset}"
            if pcol in history_filtered.columns:
                pos_value_df[asset] = history_filtered[pcol]
        
        fig_pos = go.Figure()
        colors = {"Equity": "#00d2ff", "Oil": "#ff6d00", "Gold": "#ffd600", "Bonds": "#7c4dff"}
        for asset in selected_assets:
            if asset in pos_value_df.columns:
                fig_pos.add_trace(go.Scatter(
                    x=pos_value_df["date"], y=pos_value_df[asset],
                    mode="lines", name=asset,
                    line=dict(color=colors.get(asset, "#ffffff"), width=1.5),
                    stackgroup="one"
                ))
        fig_pos.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=400, title="Position Quantities Over Time",
            xaxis_title="Date", yaxis_title="Shares / Units",
            margin=dict(l=40, r=20, t=40, b=40),
        )
        st.plotly_chart(fig_pos, width="stretch")


# ═══════════════════════════════════════════════
# TAB 4 — Alpha & Beta
# ═══════════════════════════════════════════════
with tab4:
    st.subheader("Alpha & Beta Analysis")
    
    a1, a2 = st.columns(2)
    a1.metric("Portfolio Alpha (annualized)", f"{metrics['alpha']:.4f}")
    a2.metric("Portfolio Beta", f"{metrics['beta']:.4f}")
    
    st.divider()
    
    # Rolling Alpha & Beta (60-day window)
    pv = history_filtered["total_value"].values
    port_rets = pd.Series(np.diff(pv) / pv[:-1])
    mkt_rets = df_features["equity_Returns"].iloc[-len(port_rets):].reset_index(drop=True)
    
    # Align lengths
    min_len = min(len(port_rets), len(mkt_rets))
    port_rets = port_rets.iloc[:min_len]
    mkt_rets = mkt_rets.iloc[:min_len]
    dates_rolling = history_filtered["date"].iloc[1:min_len+1].reset_index(drop=True)
    
    window = 60
    rolling_beta = port_rets.rolling(window).cov(mkt_rets) / mkt_rets.rolling(window).var()
    rolling_alpha = (port_rets.rolling(window).mean() - rolling_beta * mkt_rets.rolling(window).mean()) * 252
    
    col_alpha, col_beta = st.columns(2)
    
    with col_alpha:
        fig_a = go.Figure()
        fig_a.add_trace(go.Scatter(
            x=dates_rolling, y=rolling_alpha,
            mode="lines", name="Rolling Alpha (60d)",
            line=dict(color="#00e676", width=1.5),
        ))
        fig_a.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
        fig_a.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=350, title="Rolling Alpha (60-day)",
            margin=dict(l=40, r=20, t=40, b=40),
        )
        st.plotly_chart(fig_a, width="stretch")
    
    with col_beta:
        fig_b = go.Figure()
        fig_b.add_trace(go.Scatter(
            x=dates_rolling, y=rolling_beta,
            mode="lines", name="Rolling Beta (60d)",
            line=dict(color="#ff6d00", width=1.5),
        ))
        fig_b.add_hline(y=1, line_dash="dash", line_color="rgba(255,255,255,0.3)",
                        annotation_text="β=1")
        fig_b.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=350, title="Rolling Beta (60-day)",
            margin=dict(l=40, r=20, t=40, b=40),
        )
        st.plotly_chart(fig_b, width="stretch")
    
    # Returns scatter
    st.subheader("Portfolio vs Market Returns")
    scatter_df = pd.DataFrame({"Portfolio": port_rets.values, "Market": mkt_rets.values}).dropna()
    fig_scatter = px.scatter(
        scatter_df, x="Market", y="Portfolio",
        template="plotly_dark",
        color_discrete_sequence=["#3a7bd5"],
        opacity=0.4,
    )
    # Regression line
    if len(scatter_df) > 2:
        z = np.polyfit(scatter_df["Market"], scatter_df["Portfolio"], 1)
        x_line = np.linspace(scatter_df["Market"].min(), scatter_df["Market"].max(), 100)
        fig_scatter.add_trace(go.Scatter(
            x=x_line, y=z[0]*x_line + z[1],
            mode="lines", name=f"β={z[0]:.3f}",
            line=dict(color="#ff1744", width=2, dash="dash"),
        ))
    fig_scatter.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=400, margin=dict(l=40, r=20, t=20, b=40),
    )
    st.plotly_chart(fig_scatter, width="stretch")


# ═══════════════════════════════════════════════
# TAB 5 — Trade Log
# ═══════════════════════════════════════════════
with tab5:
    st.subheader("Trade Execution Log")
    
    if not trades.empty:
        # Filters
        f1, f2, f3 = st.columns(3)
        with f1:
            action_filter = st.multiselect("Action", ["BUY", "SELL"], default=["BUY", "SELL"])
        with f2:
            asset_filter = st.multiselect("Asset", trades["asset"].unique().tolist(),
                                          default=trades["asset"].unique().tolist())
        with f3:
            st.metric("Displayed Trades", "—")  # placeholder, updated below
        
        filtered_trades = trades[
            (trades["action"].isin(action_filter)) &
            (trades["asset"].isin(asset_filter))
        ]
        f3.metric("Displayed Trades", f"{len(filtered_trades):,}")
        
        # Color-coded dataframe
        st.dataframe(
            filtered_trades.style.map(
                lambda v: "color: #00e676" if v == "BUY" else ("color: #ff1744" if v == "SELL" else ""),
                subset=["action"]
            ),
            width="stretch",
            height=500,
        )
        
        # Trade distribution
        st.divider()
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.subheader("Trades by Asset")
            fig_ta = px.histogram(trades, x="asset", color="action",
                                  barmode="group", template="plotly_dark",
                                  color_discrete_map={"BUY": "#00e676", "SELL": "#ff1744"})
            fig_ta.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 height=300, margin=dict(l=40, r=20, t=20, b=40))
            st.plotly_chart(fig_ta, width="stretch")
        
        with col_t2:
            st.subheader("Trade Volume Over Time")
            trades_copy = trades.copy()
            trades_copy["date"] = pd.to_datetime(trades_copy["date"])
            trades_monthly = trades_copy.set_index("date").resample("ME").size().reset_index(name="count")
            fig_tv = px.bar(trades_monthly, x="date", y="count", template="plotly_dark",
                            color_discrete_sequence=["#7c4dff"])
            fig_tv.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 height=300, margin=dict(l=40, r=20, t=20, b=40))
            st.plotly_chart(fig_tv, width="stretch")
    else:
        st.info("No trades were executed during the simulation.")
    
    # Errors section
    if not errors.empty:
        st.divider()
        st.subheader("⚠️ Capital Errors")
        st.dataframe(errors, width="stretch")
